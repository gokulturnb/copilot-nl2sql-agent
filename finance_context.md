# GL Finance SQL Generation Knowledge File

## Purpose

Use this file as compact context for an LLM to generate SQL over the GL finance model.

The LLM should use this file to understand:

* which table to use,
* which columns are important,
* how tables join,
* how to filter account hierarchy levels,
* how to calculate revenue/cost/expense-style metrics,
* how to apply EWIG/community/company/project filters correctly.
* how to route **units / leasing / occupancy** vs **GL rental revenue** vs **rent potential** questions.

For a **compact column index** (table → columns), see **[Quick reference: tables and columns](#quick-reference-tables-and-columns)**. Join logic, measure definitions, and anti-patterns stay in the sections below.

## Index

- [GL Finance SQL Generation Knowledge File](#gl-finance-sql-generation-knowledge-file)
  - [Purpose](#purpose)
  - [Index](#index)
  - [Quick reference: tables and columns](#quick-reference-tables-and-columns)
    - [`GLTransactions`](#gltransactions)
    - [`GLAccount`](#glaccount)
    - [`Community`](#community)
    - [`dimCompany`](#dimcompany)
    - [`GLLedger`](#glledger)
    - [`Project`](#project)
    - [`SalesInvoiceTransactions`](#salesinvoicetransactions)
    - [`SalesInvoiceMiscChargesTransactions`](#salesinvoicemiscchargestransactions)
    - [`PayablesStateTransactions`](#payablesstatetransactions)
    - [`PayablesTransactions`](#payablestransactions)
    - [`DueAnalysis`](#dueanalysis)
    - [`ReceivablesStateTransactions`](#receivablesstatetransactions)
    - [`ReceivablesTransactions`](#receivablestransactions)
    - [`ReceivablesDueAnalysis`](#receivablesdueanalysis)
    - [`Unit_Unfiltered`](#unit_unfiltered)
    - [`UnitLeasingWithLocation`](#unitleasingwithlocation)
  - [Global hard rules (always apply)](#global-hard-rules-always-apply)
- [1. Main fact table: `GLTransactions`](#1-main-fact-table-gltransactions)
  - [Important columns](#important-columns)
- [2. Account dimension: `GLAccount`](#2-account-dimension-glaccount)
  - [Default join](#default-join)
  - [Important columns](#important-columns-1)
  - [MainAccountCategory\_Description matching rule](#mainaccountcategory_description-matching-rule)
  - [GLAccount display/account-level usage rule](#glaccount-displayaccount-level-usage-rule)
  - [GL hierarchy matching rule](#gl-hierarchy-matching-rule)
- [Payables State Transactions rules](#payables-state-transactions-rules)
  - [Important columns](#important-columns-2)
  - [Default joins](#default-joins)
  - [Payables Balance rule](#payables-balance-rule)
    - [Payables Balance by quarter (or by calendar grain)](#payables-balance-by-quarter-or-by-calendar-grain)
  - [Average Payables rule](#average-payables-rule)
    - [Average Payables by quarter (or by grain)](#average-payables-by-quarter-or-by-grain)
  - [Due Analysis Group1 rule for Payables](#due-analysis-group1-rule-for-payables)
    - [Payables Before Due](#payables-before-due)
    - [Payables Overdue / After Due](#payables-overdue--after-due)
  - [% Payables Overdue rule](#-payables-overdue-rule)
  - [Standard Payables Balance + Before Due + Overdue pattern](#standard-payables-balance--before-due--overdue-pattern)
  - [Payables DueDays bucket rule](#payables-duedays-bucket-rule)
    - [Payables due analysis presentation format (Due Overdue buckets)](#payables-due-analysis-presentation-format-due-overdue-buckets)
    - [Payables due bucket SQL pattern](#payables-due-bucket-sql-pattern)
  - [Payables vendor key rule (denormalized)](#payables-vendor-key-rule-denormalized)
    - [Pay-to vendor columns (default)](#pay-to-vendor-columns-default)
    - [Vendor Purchase on Credit physical column rule](#vendor-purchase-on-credit-physical-column-rule)
    - [Buy-from vendor columns (only on explicit request)](#buy-from-vendor-columns-only-on-explicit-request)
    - [Payables state ↔ transaction join rule](#payables-state--transaction-join-rule)
  - [Mistakes to avoid (Payables State Transactions)](#mistakes-to-avoid-payables-state-transactions)
- [3. Community dimension: `Community`](#3-community-dimension-community)
  - [Join](#join)
  - [Important columns](#important-columns-3)
  - [Confirmed EWIG rule](#confirmed-ewig-rule)
  - [Denormalized location columns on facts](#denormalized-location-columns-on-facts)
- [4. Company dimension: `dimCompany`](#4-company-dimension-dimcompany)
  - [Join](#join-1)
  - [Important columns](#important-columns-4)
- [5. Ledger dimension: `GLLedger`](#5-ledger-dimension-glledger)
  - [Join](#join-2)
  - [Important columns](#important-columns-5)
- [6. Project dimension: `Project`](#6-project-dimension-project)
  - [Join](#join-3)
  - [Important columns](#important-columns-6)
- [7. Calculation rules](#7-calculation-rules)
  - [Revenue](#revenue)
  - [Cost, expense, and other GL amounts (non-revenue)](#cost-expense-and-other-gl-amounts-non-revenue)
  - [Total Expenses rule](#total-expenses-rule)
    - [Confirmed logic](#confirmed-logic)
    - [Standard SQL pattern](#standard-sql-pattern)
    - [Example: Total Expenses for 2024](#example-total-expenses-for-2024)
  - [Debit / credit](#debit--credit)
  - [Sales / Net Sales](#sales--net-sales)
    - [Sales customer / vendor display columns (denormalized)](#sales-customer--vendor-display-columns-denormalized)
      - [Sell-to customer columns (default for sales / net sales)](#sell-to-customer-columns-default-for-sales--net-sales)
      - [Bill-to customer columns (only when AR / collection is involved on the sales fact)](#bill-to-customer-columns-only-when-ar--collection-is-involved-on-the-sales-fact)
      - [Sales + Receivables comparison rule](#sales--receivables-comparison-rule)
      - [Vendor display on sales fact](#vendor-display-on-sales-fact)
      - [Customer-name anti-pattern](#customer-name-anti-pattern)
    - [Net sales (total) — invoice model](#net-sales-total--invoice-model)
    - [Net sales by customer + receivables (top-N pattern)](#net-sales-by-customer--receivables-top-n-pattern)
    - [Item-level net sales (`ItemName`)](#item-level-net-sales-itemname)
    - [Net Sales grouping by denormalized columns](#net-sales-grouping-by-denormalized-columns)
    - [New customers (sell-to, net-sales definition)](#new-customers-sell-to-net-sales-definition)
- [Receivables State Transaction rules](#receivables-state-transaction-rules)
  - [Main table: `ReceivablesStateTransactions`](#main-table-receivablesstatetransactions)
  - [Customer Net Change rule](#customer-net-change-rule)
    - [Important columns (`ReceivablesTransactions`)](#important-columns-receivablestransactions)
    - [Confirmed formula](#confirmed-formula)
  - [Receivables Balance rule](#receivables-balance-rule)
  - [Receivables DueDays rule](#receivables-duedays-rule)
  - [Receivables Before Due](#receivables-before-due)
  - [Receivables Overdue](#receivables-overdue)
  - [Receivables Balance + Overdue + Overdue % pattern](#receivables-balance--overdue--overdue--pattern)
  - [Receivables bucket rule using DueDays](#receivables-bucket-rule-using-duedays)
  - [Average Receivables rule](#average-receivables-rule)
  - [Receivables Turnover Days rule](#receivables-turnover-days-rule)
    - [Monthly rolling-N pattern (rolling avg, rolling sum, etc.)](#monthly-rolling-n-pattern-rolling-avg-rolling-sum-etc)
    - [Monthly receivables: snapshot balance, overdue %, turnover by `YearMonth`](#monthly-receivables-snapshot-balance-overdue--turnover-by-yearmonth)
  - [Receivables customer key rule (denormalized)](#receivables-customer-key-rule-denormalized)
    - [Bill-to customer columns (default for AR)](#bill-to-customer-columns-default-for-ar)
    - [Sell-to customer columns (only when sales-flavored)](#sell-to-customer-columns-only-when-sales-flavored)
    - [Example (top 10 customers by receivables balance)](#example-top-10-customers-by-receivables-balance)
  - [Mistakes to avoid (Receivables State Transactions)](#mistakes-to-avoid-receivables-state-transactions)
- [Executive Finance KPI rules](#executive-finance-kpi-rules)
  - [1. Net Profit Margin](#1-net-profit-margin)
    - [Definition](#definition)
    - [SQL mapping](#sql-mapping)
    - [Standard SQL pattern](#standard-sql-pattern-1)
  - [2. Profitability After Direct Costs](#2-profitability-after-direct-costs)
    - [Definition](#definition-1)
    - [SQL mapping](#sql-mapping-1)
    - [Standard SQL pattern](#standard-sql-pattern-2)
  - [3. Liquidity / Current Ratio](#3-liquidity--current-ratio)
    - [Definition](#definition-2)
    - [SQL mapping](#sql-mapping-2)
    - [Standard SQL pattern](#standard-sql-pattern-3)
  - [4. Working Capital](#4-working-capital)
    - [Definition](#definition-3)
    - [SQL mapping](#sql-mapping-3)
    - [Standard SQL pattern](#standard-sql-pattern-4)
- [Denormalized display columns — pointers](#denormalized-display-columns--pointers)
- [8. Date rules](#8-date-rules)
  - [Default `DateID` window when the user gives no period](#default-dateid-window-when-the-user-gives-no-period)
- [9. EWIG selection rule](#9-ewig-selection-rule)
- [10. Standard SQL pattern](#10-standard-sql-pattern)
- [11. Confirmed query example: Total revenue by year for EWIG community](#11-confirmed-query-example-total-revenue-by-year-for-ewig-community)
- [Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules)
  - [Actual table names](#actual-table-names)
  - [Table routing rule](#table-routing-rule)
    - [Use `Unit_Unfiltered` for current portfolio / operational questions](#use-unit_unfiltered-for-current-portfolio--operational-questions)
    - [Use `UnitLeasingWithLocation` for lease / tenant / contract questions](#use-unitleasingwithlocation-for-lease--tenant--contract-questions)
  - [GLTransactions denormalized display columns](#gltransactions-denormalized-display-columns)
  - [GL rental revenue rule](#gl-rental-revenue-rule)
    - [Rental revenue by building from GL](#rental-revenue-by-building-from-gl)
    - [Rental revenue by unit from GL](#rental-revenue-by-unit-from-gl)
    - [Building performance using GL rental revenue](#building-performance-using-gl-rental-revenue)
  - [Rent potential vs actual GL revenue](#rent-potential-vs-actual-gl-revenue)
  - [Unit type demand rule](#unit-type-demand-rule)
  - [Rental growth by area rule](#rental-growth-by-area-rule)
  - [Lease expiry / renewal rule](#lease-expiry--renewal-rule)
  - [Mistakes to avoid (Real Estate / Leasing)](#mistakes-to-avoid-real-estate--leasing)
- [Vacancy, Re-let, Occupancy, and Tenant Demand Rules](#vacancy-re-let-occupancy-and-tenant-demand-rules)
  - [Table routing](#table-routing)
  - [1. Units vacant for more than 90 days](#1-units-vacant-for-more-than-90-days)
  - [2. Average time to re-let a unit in a building](#2-average-time-to-re-let-a-unit-in-a-building)
  - [3. Buildings below portfolio average occupancy](#3-buildings-below-portfolio-average-occupancy)
  - [4. Areas with highest tenant demand right now](#4-areas-with-highest-tenant-demand-right-now)
  - [Common mistakes to avoid (vacancy / occupancy / demand)](#common-mistakes-to-avoid-vacancy--occupancy--demand)
- [Tenant Stay, Tenant Revenue, and Tenant Retention Rules](#tenant-stay-tenant-revenue-and-tenant-retention-rules)
  - [1. Average length of stay for tenants](#1-average-length-of-stay-for-tenants)
  - [2. Top-revenue tenants this year](#2-top-revenue-tenants-this-year)
  - [3. Tenant retention improved in the last 12 months](#3-tenant-retention-improved-in-the-last-12-months)
  - [Common mistakes to avoid (tenant stay / revenue / retention)](#common-mistakes-to-avoid-tenant-stay--revenue--retention)
- [GL Rental Income, Rental Yield, Building Contribution, and Asset Class Revenue Rules](#gl-rental-income-rental-yield-building-contribution-and-asset-class-revenue-rules)
  - [1. Total rental income (portfolio YTD)](#1-total-rental-income-portfolio-ytd)
  - [2. Highest and lowest rental yield by property](#2-highest-and-lowest-rental-yield-by-property)
  - [3. Top-performing building income contribution](#3-top-performing-building-income-contribution)
  - [4. Asset class revenue contribution](#4-asset-class-revenue-contribution)
  - [Common mistakes to avoid (portfolio rental KPIs)](#common-mistakes-to-avoid-portfolio-rental-kpis)
- [12. Mistakes to avoid](#12-mistakes-to-avoid)
- [13. GL hierarchy tree](#13-gl-hierarchy-tree)

## Quick reference: tables and columns

Examples use **unqualified** table names; resolve **`schema.table`** from the warehouse catalog if needed.

This section is a **lookup index** only. Detailed rules, SQL patterns, and “do not” notes are under the numbered headings and domain sections (Payables, Receivables, Sales, etc.). Confirm rarely used columns in **`INFORMATION_SCHEMA.COLUMNS`**.

### `GLTransactions`

| Column | Role |
|--------|------|
| `DateID` | `YYYYMMDD` period key |
| `GLAccountID` | → `GLAccount.GLAccountDimPKID` |
| `GLNetChangeACY` | Net amount ACY (revenue: `-SUM`; non-revenue: `SUM` per global rules) |
| `GLDebitACY`, `GLCreditACY` | Debit/credit breakdown when explicitly requested |
| `CompanyID` | → `dimCompany.CompanyID` |
| `GLLedgerID` | → `GLLedger.GLLedgerDimPKID` |
| `FDCommunityID` | → `Community.FinancialDimension4ID` |
| `FDProjectID` | → `Project.FinancialDimension23ID` |
| `FDBuildingID`, `FDUnitID`, `FDCustomerID`, `FDVendorID` | Other financial dims when the question requires them |
| `BuildingName` | Building/property display and `GROUP BY` (default output; not `FDBuildingID`) |
| `UnitName` | Unit display and `GROUP BY` (default output; not `FDUnitID`) |
| `LocationName` | Location grouping **only if asked** |
| `RegionName` | Region grouping **only if asked** |

Details: **[Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules)**.

### `GLAccount`

| Column | Role |
|--------|------|
| `GLAccountDimPKID` | Primary key |
| `MainAccount_MainAccountId`, `MainAccount_Name`, `MainAccount_Type` | Account identity |
| `AccountCategory` | Category bucket (not for `MainAccountCategory_Description` matching) |
| `MainAccountCategory_Description` | Category labels — match here before L1–L7 when applicable |
| `mainaccounthierarchy-1_L1-Name` … `mainaccounthierarchy-1_L7-Name` | Hierarchy levels + codes (`…_L1` … `…_L7`) |
| `GLAccount` | Combined display account — only when user asks GL account–level output |
| `mainaccounthierarchy-1_StatementType` | Income Statement / Balance sheet / etc. |

### `Community`

| Column | Role |
|--------|------|
| `FinancialDimension4ID` | PK / join target from facts |
| `Code`, `Name` | Filter; default `cm.Code = 'EWIG'` unless user overrides |
| `DimensionCode` | Usually `Community` |

### `dimCompany`

| Column | Role |
|--------|------|
| `CompanyID`, `CompanyCode`, `CompanyName` | Company / legal entity scope |

### `GLLedger`

| Column | Role |
|--------|------|
| `GLLedgerDimPKID`, `LEDGER_NAME`, `LEDGER_DESCRIPTION`, `LEDGER_ACCOUNTINGCURRENCY` | Ledger scope |

### `Project`

| Column | Role |
|--------|------|
| `FinancialDimension23ID`, `Code`, `Name`, `DimensionCode` | Project scope |

### `SalesInvoiceTransactions`

| Column | Role |
|--------|------|
| `DateID` | Period |
| `FDCommunityID` | → `Community` (still used for EWIG join + filter) |
| `CUSTINVOICETRANS_LINEAMOUNTMST` | Invoice line amount (net sales **line** component) |
| `SellToCustomerID` | **Default customer key** for sales / net sales / new customers |
| `SellToCustomerName` | Display name (`MAX(...)` when grouping by `SellToCustomerID`) |
| `SellToCustomerCountry` | Sell-to country |
| `BillToCustomerID`, `BillToCustomerName`, `BillToCustomerCountry`, `BillToCustomerGroup` | Bill-to side (use for AR / collection joins to receivables) |
| `ItemName` | Item-level filters; see **Sales / Net Sales** for the value list |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |
| `CustomerName`, `VendorName` | Legacy denormalized names; prefer the typed `SellTo*` / `BillTo*` cols |

### `SalesInvoiceMiscChargesTransactions`

| Column | Role |
|--------|------|
| `DateID`, `FDCommunityID` | Period + community |
| `SalesDiscountAmountEnd` | Discount end — subtract in net sales (aggregate separately from lines) |
| `SellToCustomerID`, `SellToCustomerName` | Default sales customer key + display; must match line table when grouping |
| `BillToCustomerID`, `BillToCustomerName` | Bill-to side (use only when AR / collection logic requires) |
| `ItemName` | Must match line table for item-level net sales |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |

### `PayablesStateTransactions`

| Column | Role |
|--------|------|
| `DateID` | Snapshot date |
| `FDCommunityID` | → `Community` |
| `PayablesBalance` | Closing balance (use **latest** `DateID` semantics per payables rules) |
| `hPayablesBalanceSum` | Daily balance for averages |
| `DueAnalysisID` | → `DueAnalysis` for due-status / bucket measures |
| `PayToVendorID` | **Default vendor key** for payables vendor KPIs (not `FDVendorID`) |
| `PayToVendorName`, `PayToVendorCountry`, `PayToVendorStateCode`, `PayToVendorGroup` | Pay-to display / `GROUP BY` |
| `BuyFromVendorID`, `BuyFromVendorName`, `BBuyFromVendorCountry`, `BuyFromVendorStateCode`, `BuyFromVendorGroup` | Buy-from side (only on explicit request; note **double `B`** in `BBuyFromVendorCountry`) |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |

### `PayablesTransactions`

| Column | Role |
|--------|------|
| `DateID`, `FDCommunityID` | Period + community |
| `PayToVendorID`, `PayToVendorName` | Default vendor key + display (join key for state ↔ transaction) |
| `BuyFromVendorID`, `BuyFromVendorName` | Buy-from side on explicit request |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |
| `VENDTRANS_AMOUNTMST` | Vendor Net Change (transaction-level movement) |
| `VendorPurchaseonCredit` | **Vendor Purchase on Credit** physical column — note: **no spaces**, lowercase `on` (not `[Vendor Purchase on Credit]` or `VendorPurchaseOnCredit`) |

### `DueAnalysis`

| Column | Role |
|--------|------|
| `DueAnalysisID` | Join key from `PayablesStateTransactions` |
| `DueDays` | **`da.DueDays`** for payables aging buckets |
| `Group1` (and related) | Before-due / overdue flags in legacy patterns — follow payables section for current bucket rules |

### `ReceivablesStateTransactions`

| Column | Role |
|--------|------|
| `DateID`, `FDCommunityID` | Period + community |
| `BillToCustomerID` | **Default customer key** for receivables / AR KPIs |
| `BillToCustomerName`, `BillToCustomerCountry`, `BillToCustomerGroup` | Bill-to display / `GROUP BY` |
| `SellToCustomerID`, `SellToCustomerName` | Sell-to side (use when ranking sales customers + AR exposure) |
| `ReceivablesBalance` | Closing balance (snapshot / latest-date semantics) |
| `hReceivablesBalanceSum` | Daily balance for averages and turnover |
| `ReceivablesStateTransactions_DueDays` | Before-due vs overdue classification |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |
| `CustomerName` | Legacy denormalized name; prefer `BillToCustomerName` |

### `ReceivablesTransactions`

| Column | Role |
|--------|------|
| `DateID`, `FDCommunityID` | Period + community |
| `BillToCustomerID`, `BillToCustomerName` | Default AR customer key + display |
| `SellToCustomerID`, `SellToCustomerName` | Sell-to side (when sales-flavored analysis is required) |
| `CUSTTRANS_AMOUNTMST` | **Customer Net Change** — `SUM` over the period (not from `ReceivablesStateTransactions`) |
| `CustomerSalesonCredit` | Sales on credit (receivables turnover denominator) — confirm spelling in catalog |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |

### `ReceivablesDueAnalysis`

| Column | Role |
|--------|------|
| `DateID`, `FDCommunityID` | Period + community |
| `BillToCustomerID`, `BillToCustomerName` | Default AR customer key + display for due-analysis breakdowns |
| `BuildingName`, `CommunityName`, `LocationName` | Denormalized display / `GROUP BY` |

### `Unit_Unfiltered`

| Column | Role |
|--------|------|
| `UnitID` | Unit count |
| `UnitName` | Unit display |
| `PropertyID` | Property/building key |
| `PropertyName` | Building/property display (match to `GLTransactions.BuildingName`) |
| `Status` | Leased / vacant / blocked |
| `StateCode` | Active portfolio filter (`0`) |
| `UnitTypeName` | Apartment, Villa, Commercial, Parking, etc. |
| `RoomCategory` | Studio, 1 Bedroom, 2 Bedroom, etc. |
| `UsePermitName` | Residential / Commercial (asset class) |
| `UpdatedLocationName` | Area/location |
| `RentPerAnnumExcludingTax` | Rent potential / current annual unit rent (**not** posted GL revenue) |
| `TotalAreaSqft` | Area calculation |
| `HandOverDate` | Vacancy age calculation |

Portfolio rules: **[Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules)**. Do not use `UnitWithRM`.

### `UnitLeasingWithLocation`

| Column | Role |
|--------|------|
| `UnitLeasingID` | Lease/contract key |
| `ID` | Contract name/number |
| `PropertyName` | Building/property display |
| `UnitName` | Unit display |
| `ContractStart` | Lease start / demand / growth period |
| `ContractEnd` | Planned lease end |
| `ActualMoveOutDate` | Actual lease end if moved out |
| `TotalContractValueAfterDiscount` | Lease/contract value (**not** posted GL revenue) |
| `LeasingType` | New / Renewal / Transfer |
| `NextStatus` | Renewal-rate logic |
| `CorporateCustomerName`, `PrimaryContact`, `ContactType` | Tenant/customer |
| `UsePermitName` | Residential / Commercial |
| `UpdatedLocationName` | Area/location |
| `UnitTypeName`, `RoomCategory` | Unit type / room category |

Lease rules: **[Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules)**.

## Global hard rules (always apply)

1. Community filter must always be present in business-facing finance queries.
2. Default community is `EWIG` unless the user explicitly asks for another community.
3. Any money/amount output from **`GLNetChangeACY`** should be returned in **millions** by default (wrap with `CAST(ROUND(... / 1000000.0, 4) AS DECIMAL(18,4))` unless the question says otherwise). **Sign:** use **`-SUM(t.GLNetChangeACY)`** only when the question is **revenue** (credit-normal revenue accounts so the reported number is positive). For **cost**, **expense**, **asset**, **liability**, **equity**, and other **non-revenue** GL movement from the same column, use **`SUM(t.GLNetChangeACY)`** with **no** leading unary minus. Do not apply `-SUM` to every GL query by default.

Revenue (millions):

```sql
CAST(ROUND((-SUM(t.GLNetChangeACY)) / 1000000.0, 4) AS DECIMAL(18,4))
```

Non-revenue GL movement (millions, default sign):

```sql
CAST(ROUND(SUM(t.GLNetChangeACY) / 1000000.0, 4) AS DECIMAL(18,4))
```

4. Do not assume every revenue question means full `Revenue Main Group`. First map the question term to the GL hierarchy tree and then filter at the best matching level (`L1` /`L2` / `L3` / `L5` / `L7`).
5. For terms like `operating revenue`, `rental revenue`, `service revenue`, etc., resolve using the hierarchy tree nodes and filter by matching hierarchy code/name. Do not invent mappings.
6. Prefer hierarchy-name filters for readability when codes are not explicitly requested:
   - `a.[mainaccounthierarchy-1_L1-Name]`
   - `a.[mainaccounthierarchy-1_L2-Name]`  
   - `a.[mainaccounthierarchy-1_L3-Name]`
   - `a.[mainaccounthierarchy-1_L5-Name]`
   - `a.[mainaccounthierarchy-1_L7-Name]`
7. For "breakdown" questions without explicit dimension (month, project, community, etc.), default to hierarchy breakdown:
   - If selected level is `L1`, breakdown by `L2`.
   - If selected level is `L2`, breakdown by `L3`.
   - If selected level is `L3`, breakdown by `L5`.
   - If selected level is `L5`, breakdown by `L7`.
   - If selected level is `L7`, keep exact `L7` (no deeper hierarchy).
8. If user explicitly asks "breakdown by month/year/project/community", use that explicit dimension instead of hierarchy-level breakdown.
9. For large result sets, prefer returning a concise top-N/table-friendly result shape in SQL when question allows it.
10. Account/business term resolution order: (1) `MainAccountCategory_Description` if it matches the known list; (2) GL hierarchy `L1` → `L2` → `L3` → `L5` → `L7`; (3) `a.GLAccount` only when the user explicitly asks for GL account-level output or a specific GL account. Do not use `GLAccount.AccountCategory` for category-description matching.
11. **Default date window:** If the user does **not** specify a calendar year, `DateID` range, month, quarter, or a named period (YTD, MTD, QTD, WTD, last month, prior year, etc.), apply the **current calendar year through today** on `DateID`: lower bound `YEAR(GETDATE()) * 10000 + 101`, upper bound `CAST(CONVERT(char(8), GETDATE(), 112) AS INT)`. Use the fact table’s date column (e.g. `t.DateID`, `p.DateID`). If the user names a specific `20xx` year, use that year instead of this default (typically full Jan 1–Dec 31 for a past year unless the wording clearly means YTD within that year).

\---

# 1\. Main fact table: `GLTransactions`

`GLTransactions` is the main GL transaction/fact table. Start from this table for financial amount queries.

## Important columns

|Column|Meaning / SQL usage|
|-|-|
|`DateID`|Date key in `YYYYMMDD` integer format. Use for year, month, YTD, and date-range filters.|
|`GLAccountID`|Default account key. Join to `GLAccount.GLAccountDimPKID`.|
|`GLNetChangeACY`|Main accounting-currency net amount. For **revenue** questions, aggregate with **`-SUM`** so credit-side movement shows positive. For **cost / expense / other** GL totals, use **`SUM`** without a leading minus unless this file specifies otherwise.|
|`GLDebitACY`|Debit amount in accounting currency. Use only when debit is specifically requested.|
|`GLCreditACY`|Credit amount in accounting currency. Use only when credit is specifically requested.|
|`CompanyID`|Company/legal entity key. Join to `dimCompany.CompanyID` only for company filtering.|
|`GLLedgerID`|Ledger key. Join to `GLLedger.GLLedgerDimPKID` only for ledger filtering.|
|`FDCommunityID`|Community/portfolio dimension key. Join to `Community.FinancialDimension4ID`.|
|`FDProjectID`|Project dimension key. Join to `Project.FinancialDimension23ID`.|
|`FDBuildingID`|Building financial dimension key. Prefer `BuildingName` for display/`GROUP BY` unless IDs are explicitly requested.|
|`FDUnitID`|Unit financial dimension key. Prefer `UnitName` for display/`GROUP BY` unless IDs are explicitly requested.|
|`FDCustomerID`|Customer financial dimension key, if customer table is available.|
|`FDVendorID`|Vendor financial dimension key, if vendor table is available.|
|`BuildingName`|Building/property display and grouping on GL facts. See **[GLTransactions denormalized display columns](#gltransactions-denormalized-display-columns)**.|
|`UnitName`|Unit display and grouping on GL facts.|
|`LocationName`|Location grouping **only if** the user asks for location.|
|`RegionName`|Region grouping **only if** the user asks for region.|

\---

# 2\. Account dimension: `GLAccount`

`GLAccount` is the account master and account hierarchy table. Use it to classify GL transactions as revenue, cost, expense, asset, liability, equity, etc.

## Default join

```sql
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
```

## Important columns

|Column|Meaning / SQL usage|
|-|-|
|`GLAccountDimPKID`|Primary key of the account dimension.|
|`MainAccount\_MainAccountId`|Actual chart of account/account code.|
|`MainAccount\_Name`|Account name.|
|`MainAccount\_Type`|Source account type.|
|`AccountCategory`|Business account category. Useful for category-level breakdown.|
|`MainAccountCategory_Description`|Main account category description. Some report/business labels come from this field instead of L1-L7 hierarchy. Example: `Finance Charges`, `Rent,utilities & telephone`, `Business Promotion`, `Office Expenses`.|
|`GLAccount`|Combined/display account field. Do not use for normal business-term matching; use only when the user explicitly asks for GL account-level analysis or a specific GL account (see [GLAccount display/account-level usage rule](#glaccount-displayaccount-level-usage-rule)).|
|`mainaccounthierarchy-1\_L1`|L1 hierarchy code. Broadest hierarchy level.|
|`mainaccounthierarchy-1\_L1-Name`|L1 hierarchy display name. Example: `Revenue Main Group`, `Cost`, `Asset`.|
|`mainaccounthierarchy-1\_L3`|L3 hierarchy code. More specific than L1.|
|`mainaccounthierarchy-1\_L3-Name`|L3 hierarchy display name. Example: `Rental Revenue (Grp)`, `Rental Cost`.|
|`mainaccounthierarchy-1\_L5`|L5 hierarchy code. More specific than L3.|
|`mainaccounthierarchy-1\_L5-Name`|L5 hierarchy display name. Example: `Rental Revenue (Grp)`, `Building Maintenance Cost`.|
|`mainaccounthierarchy-1\_L7`|L7 hierarchy code. Most specific hierarchy level.|
|`mainaccounthierarchy-1\_L7-Name`|L7 hierarchy display name. Example: `Rental Revenue`, `General Maintenance Cost`.|
|`mainaccounthierarchy-1\_StatementType`|Financial statement type such as `Income Statement`, `Balance sheet`, `Off Balance Sheet Items`.|

## MainAccountCategory_Description matching rule

Before resolving a business/account/report term through the GL hierarchy, first check whether the user term matches one of the known `GLAccount.MainAccountCategory_Description` values.

If matched, use:

```sql
a.MainAccountCategory_Description = '<matched exact value>'
```

Do not use `GLAccount.AccountCategory` for this matching.

Only if no category-description match exists, continue with the existing L1 -> L2 -> L3 -> L5 -> L7 hierarchy matching rule. Use `a.GLAccount` for filters or dimensions only when the user explicitly requests GL account-level output; see [GLAccount display/account-level usage rule](#glaccount-displayaccount-level-usage-rule).

Known MainAccountCategory_Description values:

Deferred Revenue
"Rent,utilities & telephone"
Office Expenses
Prior Period Adjustment
Bank Loans
Retention Receivable
Finance Charges
Fair Value Reserve
Retention Payable
Land
Impairment & other Provisions
Professional fees
Interest expense
Operating Income
Notes Receivable
Property Plant & Equipment
Owners Current Account
Bank Overdraft
Capital Work-In-Progress
Repair & Maintenance-Buildings
Share Holder Contribution
Manpower cost
Pre-operating Expenses
Advance Payment Received
N/A
Perpayment & Deposits
Other Income/(Expense)
Retained Earnings B/F
Trade & Other Receivables
Advances
Cash & Cash Equivalents
Business Promotion
Provision for doubtfull debts
Notes Payable
Rents Received In Advance
Off Balance Sheet Items
Travel Expense
Direct Cost
Portfolio Valuation Gain/Loss
Accrued Interest
Investment Property
Share Capital
Provision For EOSB
Long Term Advances
Depreciation
Accounts Payable & Accruals
Advance Payment To Suppliers
Other Investment
Joint Venture Investments
Contract Work-In-Progress
Due To Affiliated Companies
Current Maturity Of Loans
Investment In Subsidiaries
Investment Held For Trading
Inventories
R & M - Equipments
Statutory Reserve
Due From Related Parties
Vehicle Expense

Matching rules:

- Ignore case and extra spaces when matching.
- Keep the final SQL literal exactly as shown in the known list.
- If the user says finance charges, match Finance Charges.
- If the user says rent utilities telephone, match Rent,utilities & telephone.
- If the user says business promotion, match Business Promotion.
- If the user says office expenses, match Office Expenses.

Examples:

-- Finance Charges
a.MainAccountCategory_Description = 'Finance Charges'

-- Rent,utilities & telephone
a.MainAccountCategory_Description = 'Rent,utilities & telephone'

-- Business Promotion
a.MainAccountCategory_Description = 'Business Promotion'

-- Office Expenses
a.MainAccountCategory_Description = 'Office Expenses'

If the user asks broad hierarchy terms like Revenue, Rental Revenue, Rental Revenue Group, Gen & Adm Expenses, or Direct Cost, use the existing L1-L7 hierarchy logic unless the phrase exactly matches a category description.

## GLAccount display/account-level usage rule

`GLAccount` is a combined/display account field.

Do not use `GLAccount` for normal business-term matching.

Use `GLAccount` only when the user explicitly asks for GL account-level analysis or a specific GL account.

Examples where `GLAccount` should be used:

- top 10 GL accounts by rental revenue
- GL account wise revenue
- breakdown by GL account
- show GLAccount for Finance Charges
- total for GL account `<specific account name/code>`

For GL account breakdown, select and group by:

```sql
a.GLAccount
```

Example:

```sql
SELECT TOP 10
    a.GLAccount,
    CAST(ROUND((-SUM(t.GLNetChangeACY)) / 1000000.0, 4) AS DECIMAL(18,4)) AS RentalRevenue_Mn
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
  AND a.\[mainaccounthierarchy-1\_L7] = '4111111'
GROUP BY
    a.GLAccount
ORDER BY
    RentalRevenue_Mn DESC;
```

For specific GLAccount filtering, use exact match if known:

```sql
a.GLAccount = '<exact GLAccount value>'
```

or `LIKE` only when the user provides partial text:

```sql
a.GLAccount LIKE '%<user text>%'
```

Resolution order for account/business terms:

```text
MainAccountCategory_Description first
→ GL hierarchy L1-L7
→ GLAccount only if explicitly asked for GL account
```

Known `GLAccount` values (full list; use for exact `a.GLAccount = '…'` / `LIKE` when the user names a specific display account):

1131117002 - Differed Revenue
1131115011 - Due From-Dusit Thani Abu Dhabi Hotel Llc
1131116005 - Provision Against Flamingo Advance
1131115035 - Due From-Calibers Industry LLC
1131115051 - Due from - Travel Retail Sales & Services
1131115052 - Due from - Emirates Strategic Investment Company
1131316008 - Deposit SCB
1211111001 - Investment In Bond Investments
1211111006 - Investment In Ewig
1251216003 - Accudep, Equiments (IP)
1261416005 - Vehicle Equipment
1261454001 - Accudep Computers
1111114001 - Abu Dhabi Commercial Bank
1111211004 - Cash In Transit
6111111009 - Pension Expense
6111711022 - Consumables Exp
5121511006 - Custom Duty & Freight Charges
5121113003 - Visa Expenses Renewal (Direct)
6121113001 - Lc Charges
6121115001 - Mortgage Fees  Expenses
6131111001 - Ip Building Depreciation
2121111009 - Maintenance Deposit Payable
2121111020 - Green Forest Catering Services & Ready Meals Llc-Consignment
2121111027 - Lease Liabilities (Right-of-use assets)
2121113006 - Due To- Calibers Recruitment
2121113015 - Due To- United Design International
4121311002 - Sales of Doors
4121512001 - Retail Commission Income
3111711014 - United Supplies
3111311003 - H.H. Palace & Villa Expense
3111311005 - Al Manara Palace - Owners A/C
2131111001 - Al Hilal Bank Loan - ST
4191111002 - Immigration Reimbursement
2141111008 - 2141111008
2141111009 - 2141111009
112 - Short Term Investment
1131114 - Provision/write off Against Retention rec.
21411 - Deferred Revenue  (Grp)
4121211 - Income from Labour supply
4121711 - Taxi Operating Revenue
41219 - Media & Publication Revenue
51211 - Manpower Cost (Direct)
5121113 - Other Manpower Cost (Direct)
5122011 - Taxi Operation Cost
61115 -  Professional Fees
41511 - Dog Training  Service
1131117003 - Accrued Income - Revenue
1131115034 - Due From-Calibers Recruitment Services
1131115057 - Due from Al Maryah Bank
1131314005 - Deposit - National Media Council -Jazira Mag
1131213001 - Prepaid Fidelity & Money Insurance
1131213021 - Prepaid - Sukuk Issuance Cost (amortization)
1221211001 - Reisco - Capital Plaza
1211112011 - S.P.S United Investment
1251214002 - Accdeop Decoration & Renovation (IP)
1231113005 - Rabaya Qatar Investment- Share Of P/L
1261313001 - PPE Accudep Buildings
1261413002 - Automobiles
1261415001 - Software
1261451003 - Accudep Cng Component
1111112001 - National Bank Abu Dhabi
1121111002 - Quoted Local Shares - UG Investments
1141211004 - Provision for supplier
6111112001 - End Of Service Benefits
6111113001 - Recruitment Expenses
6111113018 - Covid Test (Indirect)
6111111007 - Transportation Allowance
5121611001 - Machinery Cost
5121711001 - Designing Cost
5121511007 - Business Travel Expenses
2121111008 - Consignment Payable
2121111012 - Arabian Flowers -Consignment Vendor
2121111024 - 57 tower Corp
2121113031 - Due to - Tasameem Construction
2121113035 - Due to - Planet Tax Free
4121111001 - Contract Income
4121511008 - Gulf Greetings-Consignment Vendor Sales
4121512005 - Rebates
4121512009 - Registration Fee
2241114003 - Retention Accounts payable - Tenents
2211117001 - Sukuk (2019-24)
4191311006 - Asset Dispossal Advertisement
4141111001 - Income From Share Trading
2121116001 - VAT Payable
1131121002 - Reverse charges VAT Receivable
11213 - Quoted Overseas Shares
1241112 - Provision Against Investment
1261112 - Impairment for PPE Land
1261457 - Accudep Air Craft
2221211 - Accrue Pension-UAE Staff
411 - Rental Revenue (Grp)
412 - Service & Trading
4191611 - Income From Amortization of Differed Revenue
51112 - Property Management Cost
5111211 - Property Management Cost
51311 - Cos  Of Income From Sale Of Propertied
1131114002 - Write off Against Retention rec.
1131115064 - Due from Changer
1131314003 - Deposit For Absconding Emp
1131213014 - Prepaid Visa Charges
1131214001 - Employees Account- Others
1131215002 - Credit Note Receivables (Suppliers)
1231111003 - Libya Project
1231112002 - Provision For Bad Debt Libya Project
1261311001 - PPE Buildings-
6111113011 - Accomodation Expenses
6111911003 - R & M Fax M/C
6111911006 - R & M Equipments
6112111001 - Quoted Impairment
6111511016 - Court Fees
5121211001 - Material Cost
5121511005 - Bank Charges Guarantee/LC
5121112005 - Air Ticket Expenses
6121112001 - Term Loan Interest Fgb
2121116005 - Corporate Tax Payable2121115005
2121113022 - Due To- Select Market - Arabian
2121113050 - Due to Changer
4151111006 - Dog Training Service Individual - Intermediate
4121511002 - Al Farah Butchery  -Consignment Vendor Sales Sales
4121511009 - Al Farah Food Store-Consignment Vendor Sales
4111211001 - Property Management Revenue
3111711015 - Emirates African Investment Company L.L.C.
3111311025 - Liwa - Esic Dividend
3111211002 - General Reserve
127 - Deferred Tax Asset
3111411 - Retained Earnings (Grp)
11412 - Capital Work in Progress
1211112 - Other Investment
1261415 - Software
1261455 - Accudep Software
4141111 - Income From Share Trading
5111111 - Preventive Maintenance Cost
51216 - Machinery & Tools Cost
6111213 - Water & Electricity
7111111 - Off Balance Sheet Items...
1131115001 - Due From-Yas Health Care
1131115045 - Due from Cititrade KSA
1131115053 - Due from Al Reef 2 Al Samha
1131115054 - Due from - Grove Landscaping
1221211014 - International Golden Group (Igg)
1221411008 - Provision For Unquoted Invt - Gulf Opp
1231111002 - Sjm Project - Burj Khalifa Land
1261411003 - CNG Component Kit
1121311001 - Quoted-Overseas Shares
1141311002 - Development WIP Construction Cost
6111111005 - Overtime Expenses
6111111008 - Telephone Allowance
6111911010 - Product Support & Maintenance
6112011002 - Bad Debt Libya Project
6111711010 - Office Expense
6111711024 - Employee engagement program
6111811005 - Other IT related exp
5111111001 - Preventive Maintenance Cost
5122411001 - Dog Food
5121113002 - Visa Expenses New (Direct)
2121111028 - ACCUMULATED AMORTIZATION - ROU
2121113007 - Due To- Calibers Contacting Llc
2121113014 - Due To- Select Market
2121113019 - Due To- Select Market - Desert
2121113027 - Due to- Tasameem Real Estate
2121113030 - Due to-Rabaya Qatar
2121113032 - Due to-Bakers Crust
2121212003 - Accrued Doctor Fee
4151111005 - Dog Training Service Individual - Basic
4121311004 - Sales of Kithen Cabinets
3111711037 - East & West Properties - SHA
3111311011 - Al Wathba Stud Farm - France
3111311013 - Al Manara Palace Bank
2211111003 - FAB LOAN USD 77M
4191511001 - Interest Income
4191111004 - Other Income - Emirates Id
1131121001 - VAT Receivable
2141111018 - 2141111018
1271111 - Deferred Tax Asset
11112 - Cash Balances
1251111 - IP Land
12212 - Unquoted Local Shares - Long Term
1251212 - IP Accudep. Buildings
1261311 - PPE Buildings-
1261458 - Accudep Equipment Medical
41111 - Rental Revenue (Grp)
61114 - Vehicle Expenses
6111511 -  Professional Fees (Grp)
61312 - Depreciation For Pp
1111119 - Dubai Islamic Bank
1131116002 - Provision Against Related Party - Al Oboor
1221211011 - Provision For Unquoted Invt - Alqudra
1221211022 - Reem Investment
1221411002 - Venture Investors Fund
1211111008 - Investment In Tawasul Transport
1211112006 - Investment In Fly Abu Dhabi Air Lines Llc
1251311001 - IP Work In Progress
1141211001 - Capital  Work in Progress.
6111112010 - Annual Leave Provision
6111113010 - Consultancy Expenses
6111711020 - Packing Materials
6111511007 - Other Govt Expenses
5121811004 - Cost of Sales-Others
6131211015 - Depreciation Printers
6131211020 - Depreciation Machinery
2121111016 - Green Forest(Kaf)-Consignment Vendor
2121113041 - Due to Motopro Auto Service LLC
2121211001 - Accrued  Expenses- Others
4121511004 - Bakers Crust -Consignment Vendor Sales
3111711007 - Deco Design
3111311021 - HH - ESIC Acct
4191311005 - Asset Dispossal Maintenance
1111211 - Account  Petty Cash
1261312 - Lease Hold Improvement PPE
11311 - Accounts Receivables
1221211 - Unquoted Local Shares - Long Term
125 - Investment Properties -IP
1251214 - IP Accudep,Impairment Buildings
1261211 - Land Advances (Grp)
22212 - Accrued Pension
2231111 - Deferred Revenue Long Period
51 - Direct Cost
61 - Gen & Adm Expenses (Group)
613 - Depreciation
2 - Liabilities
1111120 - Abu Dhabi Islamic Bank
1131115008 - Due From-East & West Int'L Group L.L.C.
1131115018 - Due From-Manzel Real Estate-Bmtc
1131115026 - Due From-Baker Crust
1131115038 - Due From-United Int'l Representation Companies
1131115065 - Due from East & West Properties
1131115071 - Due from EAST & WEST PROPERTIES 3 SPV LIMITED
1131316005 - Deposit - Telephone
1131316010 - Deposit - Bank
1221211020 - Thuraya Satellite
1211112003 - Investment In East West Properties
1211111014 - Share Capital - Dusit Thani
1211112012 - United Tina - Investment
1261453002 - Automobiles Depreciation
1261456006 - Accudep Workshop Equipments
1261454004 - AccuDep - Monitor PC
1111113002 - Tasameem Bank for cheque Realization
6111112004 - Bonus
6111113015 - Other Manpower Cost
6111113007 - Security Charges Expense
6111111010 - Job Allowance
6111611001 - Advertisement
5111112003 - Elevator & Cradle Maintenance
5111116004 - Land Rent
5121911002 - Lab Consumables
2121113024 - Due To- Baker Street
2121211010 - Project - Accrued Payable for Goods Received but not Invoice
4121911001 - Media & Publication Revenue
3111711005 - Calibers Cleaning
3111711035 - Grove Landscaping
3111311026 - Emirates Coin Investment LLC
3111611001 - Revaluation Of Fixed Assets
2211115001 - Margin Trading  Account
2141111015 - 2141111015
51224 - Dog Training Service Cost
1121411 - Unquoted Overseas Investments
12111 - Investment In Subsidiaries
1241111 - Other Investment Long Term
1251216 - IP Accudep, Fur & Fix.
21 - Current Liabilities
41916 - Income From Amortization of Differed Revenue
51213 - Sub Contract Cost
51219 - Healthcare Cost (Grp)
2211213 - Accrued Interest LT,Hilal
1261511 - PP-WIP
1131114001 - Provision off Against Retention rec.
1131115056 - Due from Motopro Auto Service LLC
1131213016 - Prepaid Fire Insurance
1131214003 - Employees Account - HRA Advance
1221211027 - Unquoted Local Shares - Revaluation
1251112001 - Impairment for IP Land
1261611001 - Right-of-use assets
1261411002 - Cert Taxi Meter
1261412002 - Office Interior Decoration
1261414001 - Computer
1111116001 - Standard Chartered Bank  (SCB)
6111113016 - Contingency Exp
6111111002 - House Rent Allowance
6111211002 - Service Charges - Office Rent
6111212007 - E-life TV
5121411001 - Rent Expenses (Direct)
5121511001 - Projects Transportation Expenses
5121111006 - Uae National Allowance
5121112007 - Notice Pay
5121113006 - Medical Malpractice Insurance
2121113036 - Due to - Travel Retail Sales & Services
2121113042 - Due to Al Maryah Bank
2121211003 - Accruals Expenses-Audit Fees
4151111007 - Dog Training Service Individual - Advance
4121811001 - Workshop Taxi Autopart Revenue
4121114002 - Maintenance Inocme Preventive
4121511005 - Emirates Farms Lap-Consignment Vendor Sales
3111711001 - Share Holder ContributionDas Holding Llc
3111311004 - Hh Pvt. Affairs Office
3111311007 - Engineering Office For Hh
3111311008 - French Farm
3111311022 - Al Maryah Bank-MBank
2211118001 - CBD loan account
4191611002 - Income From Amortz. Mussafa BMTC Deferred Revenue
4191111010 - Income from sale of scrap
1131120 - Other receivables
5121811 - Cost of Goods Sold Retails
1131113 - Retention Receivable
1131213 - Prepaid Others
12 - Non Current Assets
12613 - PPE Buildings
2111112 - Adcb OD
21211 - Accounts Payable, Accruals
21312 - Accr. Interest St
2141112 - Deferred Income
31111 - Share Capital Group
6111111 - Admin Staff Payroll Cost
614 - Impairment
1131115024 - Due From-Select Market - Arabian
1221211023 - Rasmala Capital Investment
1231112001 - Prov. Agnst Invest In Jvs
1211112001 - Union Insurance
1211111024 - Investment in Al Dar Share and Bond
1251211001 - Buildings (IP)
1261452003 - Accudep Preliminary Exp
1261419001 - K9 Dogs
6111112014 - Notice Pay Admin
6111911005 - R & M Others
6111211004 - Finance Cost - Lease (ROU)
6111211005 - Amortisation of Right of use assets
6111711019 - Fire & Perils Insurance
5111112004 - Fire Fighting & Fire Alarm Maintenance Expense
5121511015 - Laundry cost
6121112004 - Term Loan Interest Ahb
6121112008 - Term loan Interest - ENBD
2121113028 - Due to-Yas Healthcare
4121511007 - Green Forest(Kaf)-Consignment Vendor Sales
4121512012 - Leaflet AD Support
3111711025 - Dusit Thani FFE Reserve
3111311001 - Owners Current Account
3111511003 - Deferred Tax Expense - OCI
2221112003 - Accrued End Of Service Benefit Labours
2221211001 - Accrued Pension UAE
4191411001 - Income from JV & Associates--
4191111008 - Bounced Cheque Fee
6111113017 - Medical Expenses
2121113059 - Due to EWPD - East West property Development
2141111013 - 2141111013
2141111017 - 2141111017
11 - Current Assets
1141211 - Capital Work in Progress.
117 - Other Current Assets
11711 - Other Current Assets(Grp)
3111311 - Owner Current Account (Grp)
4111211 - Property Management Revenue
5111113 - Security Guard Cost
5122111 - Workshop Cost
51223 - Government Contract Cost
6111212 - Telephone & Internet Expenses
1261419 - Biological Assets
1131118001 - Notes Receivables- Tenents
1131115006 - Due From-United Design Int'L
1131115030 - Due From-Flyzone Travels & Tours
1131115062 - Due from Coral Yachts
1131214009 - Employee Account – EOS Advance -EOS
1131214008 - Employees Account - Corp Credit Card
1221411009 - Provision For Unquoted Invt - Talat Mu
1241112001 - Provision Against Investment -Etisalat Misr
1251216001 - Accudep. Fur & Fix (IP)
1261416006 - Workshop Equipments
1111125001 - Ruya Bank
1141111001 - Contract Work In Progress
6111112007 - Air Ticket Expenses
6111113006 - Staff Uniforms
6111811001 - Office Maintenance
5111116005 - Property Valuation Fee
5111211001 - Property Management Cost
5121811001 - Cost of Goods Sold Retails
5121112002 - End Of Service Benefit
5121113005 - Misc. Accommodation Cost (direct)
6121114002 - Other Finance Cost
6121116002 - Sukuk Issuance Cost (2019-24)
2121115005 - Advance from Customer
2121111001 - Accounts Payable Suppliers/contractors
2121111023 - Aabar-Investment
4121111002 - Preventive Income
4121512013 - Damage/Expiry Write Off
4121611006 - Discount - Deductables
3111711029 - Bakers crust
3111711033 - Camelia Flowers
3111311017 - HH Spain Project
3111111001 - Paid In Capital
2241114002 - Retention Accounts payable - Contractors
4191311004 - Gain/Loss On Disposal
2211215 - Accrued Interest LT,SCB
1131212 - Prepaid Medical Insurance
1131312 - Deposit Against Rent
211 - Od Account-Group
2111111 - Fgb OD
3111611 - Revaluation Of Fixed Assets (Grp)
41212 - Income from Recruitment Services
4121411 - Income from Design & Fit outs
4122011 - Hotel Operation Revenue
5121311 - Sub Contract Cost
61118 - Repair & Maintenance - Building - Offices
1131120004 - Accrued receivables for Goods received but not invoiced
1131115023 - Due From-Select Market - P9
1131115028 - Due From-Southern Sun Hotel Abu Dhabi
1131115041 - Due From-Camelia Flowers & Events
1131314002 - Refundable Deposit -Others
1131211001 - Prepaid Office Rent
1131218008 - Prepaid Amc
1131213013 - Prepaid External Quality
1131214007 - Employees Account - Control Account
1221211016 - Al Qudra Holdings
1231111001 - Kazakhstan Joint Venture
1251214001 - Accudep Impairment for IP Buildings (IP)
1211112007 - Investment In Al Wathba Stud Farm
1211112009 - Investment In Emirates Africa - Proj
1211111026 - Investment in Grove
1231111004 - Invest In & Receivables - JVs
1231113008 - Citiscape Investment - Saudia
1121111004 - Quoted Shares – Portfolio
6111113004 - Visa Expenses Renewal (Direct)
6111911004 - R & M Photocopy Machine
6111611008 - Building Models
6111311005 - Business Travel Expenses
6111711003 - Subscription Fees
6111711005 - Printing & Stationery
5111114002 - Cleaning Material - Building
6131211004 - Depreciation Vehicles
2121111015 - Fresh Fishing Fish Td-Consignment Vendor
2121113021 - Due To- Select Market - P9
2121113029 - Due to-United Int'l Representation Companies
2121113054 - Due to Mohamed Sultan AI Nuaimi Advocates & Legal Consu
2121113058 - Due to EAST & WEST PROPERTIES 3 SPV LIMITED
2121212006 - Accrued Bonus
4121113001 - ManPower Income
3111711009 - Green Tree
3111711040 - Tawasul Adjustment
2211212001 - Accrued Interest LT,Adcb
4191111003 - Termination By Tamim
4191111009 - Asset Mngt & Advisory Services
1131120001 - Other receivables
6111212004 - Blackberry Rental Charges
1261313 - PPE Accudep Buildings
1261452 - Accudep Furniture & Fixture
1 - Asset
113 - AR, Prepayment, Deposits
1131111 - Trade Receivables
11312 - Prepayments
1131311 - Bank Guarantee Deposits
11411 - Contract WIP
1261315 - Impairment for Buildings (PP)
4121311 - Income from Industry Services
51221 - Workshop Cost
513 - Cos  Of Income From Sale Of Propertied
2211117 - Sukuk
1131111004 - Inter-Unit Receivable
1131115069 - Due from Aed Stable Coin
1131213015 - Prepaid Trade Licence Fees
1211111002 - Investment In United Supplies
1211111018 - Investment in Caliber Recruitment
1261111001 - PPE- Land
1261211001 - Land Advances
1111211003 - Cash Advances - Others
6111911012 - Other Cleaning Expenses
6111511004 - Service Charges
6111511009 - Legal Translation Charges
5111114006 - Waste Disposal
5122411002 - Dog Medicine
5121811003 - Purchase expenditure for product
6131211002 - Depreciation  Fleet
6131211019 - Depreciation Tools & Equipments
2121113055 - Due to Emirates Coin
3111711023 - Yas Health Care
3111711038 - Emirates International Facility Management (Saudi Br)
3111311010 - Hh Morocco Villa
3111311019 - HH East & West Properties SNC
3111311024 - Ruya Community Islamic Bank
3111411002 - Dusit Thani - Retained Earnings
3111211001 - Statutory Reserves
2211113001 - Adcb Bank Loan
2141112002 - Deferred Revenue- Subscription & Distribution
1111115 - Al Hilal Bank
12512 - IP Buildings-
11211 - Quoted Local Shares
1131211 - Prepaid Rent
1221111 - Quoted Local Shares - Long Term
212 - Account Payable, Accruals
21311 - Short Term Loans
2231211 - Other Non-current Long term liabilities
4111111 - Rental Revenue
419 - Other Income
5121411 - Rent Expenses (Direct)
61112 - Rent & Utilities
61120 -  Provision For Bad Debts
1111118 - Commercial Bank of Dubai -(CBD)
711 - Off Balance Sheet Items.
1131115005 - Due From-Calibers Contracting Llc
1131215003 - Prepayment to Contractors/Suppliers
1221411007 - Investcorp - Gulf Opp - Usd
1261454002 - Accudep Printer
1111211002 - Cash Advances - Petty Cash
6111411007 - Other Vehicles Expenses
6111511003 - Other Consultancy Charges
6111511014 - Valuation Expenses
6111711006 - Charity & Contributions
6111711018 - Public Liability Insurance
5121311001 - Sub Contract Cost - Group companies
5121311002 - Sub Contract Cost - External
5122411004 - Dog Vaccination
5121511003 - Water & Electrcity (Direct)
5121111003 - Transportation Allowance
5121113001 - Uniform Expenses
6131211007 - Depreciation  Software
6131211010 - Depreciation Decoration & Renovation
6121112003 - Term Loan Interest Adcb
2121115001 - Award Payables
2121113043 - Due to Turquoise Invt
4121512007 - Promotor Charges
3111711002 - Al Arabia
3111711016 - Alarabiya Owner Account(Old)
3111711030 - Southern Sun Hotel FFE Reserve
3111311014 - Hh Pvt. Affairs Office-Car Maintenance
2231111005 - Deferred Income- Sothern Sun
2211214001 - Accrued Interest LT-CBD
2131211001 - Accrued Interest Sukuk (2019-24)
4191611001 - Income From Amortz. Manazel Mall Deferred Lease
4191711001 - Realized Current Loss/Gain
4191111001 - Other Income
7111111003 - LC Opened  -  Bank
2141111014 - 2141111014
1131115 - Due from Related Parties
11111 - Bank Balance
1111114 - Abu Dhabi Commercial Bank
1151111 - Inventory (grp)
122 - Long Term Investment
12214 - Unquoted Overseas Shares - Long Term
1261417 -  Air Craft
2121212 - Accr. Employees Bin. St
4121114 - PMU
4121512 - Othe Operation Income
41911 - Other Income
4191211 - Dividend
41915 - Interest Income
511 - Rental Cost
6112111 - Portfolio Impairment- (Grp)
6121111 - OD Interest
6131111 - Depreciation For Ip
3 - Equity Main  Group
2211114 - Al Hilal Bank Loan   LT
12616 - ROU
7 - Off Balance Sheet Items
1131115007 - Due From-Tawasul Transport Llc
1131115014 - Due From-Bond Investment
1131115033 - Due From-Flamingo Advance
1131213010 - Prepaid Public Liability Insurance
1221211009 - Sawaeed Investments
1221211015 - Al Ain Farms For Livestock Production
1211111005 - Investment In Ugh
1261456003 - Accudep Office Equipment
1121111005 - Quoted shares – Portfolio - Revaluation
6111112002 - Utility Allowance
6111811003 - Office Cleaning Expense
6111212001 - Telephone / Fax
6111511012 - Consultancy Expenses
6111711016 - Money Insurance
6111711017 - Medical Equipment Insurance
5121911006 - Medical Equipment Service Contracts
5122411006 - Dog Training Consumables
5121112004 - Bonus (Direct Admin)
6131211005 - Depreciation Computers
2121113040 - Due to - United International Dynamics Trading
2121113045 - Due to Sierra Investments LLC
4121611002 - OP Clinic - Consultation
4121512011 - Promotion Support
3111711021 - MotoPro Autoservice
3111311006 - Fleet Management Services
3111511001 - Fair Value Reserve
2211213001 - Accrued Interest LT, Hilal
N/A
2141111011 - 2141111011
4191411 - Income from JV & Associates-
1231112 - Prov. Agnst Invest In Jvs
1251215 - IP Furniture, Machinery & Others
2141111 - Deferred Rental
41912 - Dividend
5121511 - Other Direct Cost
61119 -  Repair & Maintenance - Equipment
6121114 - Processing Fees
1131121 - Tax Receivable
1261611 - ROU-
4141211 - Portfolio Valuation Gain/ Loss
2211119 - ENBD-Facility loan
1131113001 - Retention Receivable
1131115020 - Due From-Select Market - APT
1131115055 - Due from - United International Dynamics Trading
1131211003 - Prepaid Rent Warehouse
1131214004 - Employees Account - Car Allow Advance
1211111003 - Investment In Green Tree
1211111004 - Investment In Calibers Contracting
1211111027 - Investment In Changer
1261452001 - Accudep Furniture & Fixture
1261457001 - Accudep Embraer Air Craft
1111117001 - Emirates-NBD
6111611005 - Business Development
6111212003 - Lease Line-Etisalat
6111711001 - Pantry Expenses
6111711004 - Postage & Courier
6111911008 - Telephone Instrument
5111116006 - Service Fee
5111112005 - Check out – Repairs & Maintenance
5131111001 - Cos  Of Income From Sale Of Propertied
5121211002 - Inventory Profit/Loss Account
6121111002 - Od Interest Adcb
2121111003 - Rent Payable to Owner of Managed Prop
2121111018 - Al Farah Food Store-Consignment Vendor
2121113002 - Due To-Ugh Payable
2121113005 - Due To- Manazel Real Estate
2121113017 - Due To- Deco Design International
2121113018 - Select Market APT (Inter Branch)
2121113025 - Due To- Baker Crust
2121113047 - Due to Coral Yachts
2121113049 - Discount against Due to RP
4121311003 - Sales of Cabinets
4122011001 - Hotel Operation Revenue
4121111003 - General Maintenance Income
4121111006 - Facility Service Revenue
4111111005 - Parking Charges
3111711027 - Southern Sun Hotel    Fund Transfer
3111311023 - UIRC Acct Settlement
3111211003 - Merger Reserve
4191711002 - Unrealized Exchange Loss Account
7111111001 - Guarantee - Bank
2141111012 - 2141111012
6141111 - Impairment..
11212 - Unquoted Local Shares
1131117 - Accrued Income
1131118 - Notes Receivables
114 - WIP
124 - Other Investment Long Term
1261314 - PPE Accudep. Leasehold Improvement
1261413 - Vehicles-
1261456 - Accudep Office Equipment's
2121112 - Notes Payable (Grp)
2131111 - Al Hilal Bank Loans - ST
22 - Non Current Liability
31114 - Retained Earnings-
41211 - Facility Management Revenue
4191511 - Interest Income
51111 - Building Maintenance Cost
6111911 -  Repair & Maintenance - Equipment(Grp)
6121115 - Mortgage Fees  Expenses (Grp)
41412 - Portfolio Valuation Gain/Loss
1131120002 - Control Account
1131115017 - Due From-Manazel Real Estate - Select Express
1131115066 - Due from Ruya Community Islamic Bank
1131316004 - Adcp - Security Deposit - Warehouse Auh
1131213018 - Prepaid Legal Fees
1211111020 - Investment in Yassat International Morroco
1261416001 - IT - Equipments & Networking
1121111001 - Quoted Local Shares - E& W Properties
6111112009 - Furniture Allowance
6111911001 - R & M Computers
6111411003 - Vehicles Insurance Expenses
6111411005 - Vehicles Parking Expenses
6112211001 - Preoperative Rent
6112211004 - Preoperative Expenses- Others
6111213001 - Electricity Charges
6111711008 - Insurance Others
5121111007 - Special Allowance
5121111009 - Cost of Living Allowance
6131211008 - Depreciation Office Equipment's
2121111021 - BUTTERFLY LLC- Consignment Vendor
2121111025 - Arabtech Construction
2121211004 - Accruals Expenses-Utilities
4121411003 - Income from Sepervision
3111711003 - Bond Investment
3111711011 - Tawasul
3111311002 - Owners Dividend
2231111003 - Deferred Revenue - Manazel-Mall
2221111002 - Accrued End Of Service Benefit UGH
2211114001 - Term Loan other
2141111005 - Deferred Income - Facility Service
4191311002 - Asset Disposal Revenue Fleet Vehicle
4191111005 - Prop. Service Revenue
2121116003 - Reverse charge VAT Payable
1121111 - Quoted Local Shares
1121211 - Unquoted Shares
1131216 - Prepaid Vehicle Insurance
11511 - Inventory (grp)
1261111 - PPE- Land
21111 - Od Account-
222 - End of Service Benifit
2221212 - Accrued Pensione-GCC Staff
31 - Equity  Group
41218 - Workshop Revenue
4191111 - Other Income
5111116 - Other Building Cost
5122211 - Hotel Operation Cost
1131115009 - Due From-Select Market
1131115021 - Due From-Select Market - Desert
1131115042 - Due from-City Real Estate Registration
1131115050 - Due from - Emirates & Morocco Trading & General Investment
1131316007 - Deposit- Building Permit
1131211002 - Prepaid Rent Staff/Labour Accommodation
1131214002 - Employees Account - Salary Advance
1221211003 - Ug Investments
1261418003 - Medical Instruments
1261414002 - Printer
1151111002 - Inventory for goods received but not invoiced
6111111006 - U.A.E. National Allowance
6111611007 - Al-Arabia Restructuring Exp.
6111211003 - Warehouse Rent
6111511002 - Legal Fees
6111511017 - Current Tax Expense - Corp
6111711011 - Blackberry & Other Devices
5111116003 - Tawtheeq Fee
5121911004 - Medical Waste
5122411003 - Dog Medical Treatment
5121811002 - COGS- Consignment Suppliers
5121113010 - Covid Test(Direct)
6131211013 - Depreciation Workshop Equipment
6121116001 - Finance Cost Sukuk (2019-24)
2121111002 - Cr Notes Payable
2121113009 - Due To- Tawasul Transport Llc
2121113057 - Due to EAST & WEST PROPERTIES 2 SPV LIMITED
2121212010 - Accrued EOSB - UGH
4121611005 - Radiology Sales
4122111001 - Income From Government Contract
4111111008 - Transfer Contract Fee
3111711013 - United Design International
3111311012 - Horses Stable
2221111001 - Accrued End Of Service Benefit Admin
2221212001 - Accrued Pension GCC
1251211 - IP Buildings
5121812 - Commercial & Other Discount
1121511 - Other Short Term Invest
1131116 - Provision/write off Against Group copany Rec.
113121 - Account (Grp)
41112 - Property Management Revenue
4121911 - Media & Publication Revenue
5121111 - Payroll Cost
611 - Gen & Adm Expenses (Sub-Group)
61111 - Manpower Cost
61121 - Portfolio Impairment
1131111002 - Credit Card Receivable
1131115016 - Due From-Manzel Real Estate-Interest
1131115068 - Due from Emirates Coin
1131311001 - Deposits - Letter Of Guarantee
1131313001 - Water & Electricity Deposit
1221211026 - Provision For Unquoted Invt - Reisco
1211111009 - Investment In I Media Intergrated Media
1211111011 - Investment In Eifm
1231111005 - Share Profit from JV
1261412003 - Preliminary Expenses (EIFM New Office)
1111118002 - E-Dirham- (CBD)
1141211003 - Provision against CWIP
6111113008 - Staff Conveyance
6111511010 - Clinic License Expenses
5111114001 - House Keeping
5111114003 - External Glass Cleaning
5111115002 - Water Expenses
5111116007 - Building Cost - Other
5121611004 - Depreciation Tools & Equipments  ( Direct Cost)
5121511010 - Insurance Others - Direct
6121113003 - Credit Card Charges
2121111011 - Al Farah Butchery  -Consignment Vendor
2121111022 - Import Charges Payable
2121111029 - LEASE LIABILITY - OFFICE RENT
2121113034 - Due to - I Media
2121212005 - Accrued Leave Salary Labour
4121114003 - Maintenance Inocme General
4121511001 - Sales
4121511012 - BUTTERFLY LLC- Consignment Vendor Sales
3111711024 - Calibers Industry - FT
3111711028 - Southern Sun Hotel     Profit Transfer
2211211001 - Accrued Interest LT,Fgb
7111111002 - Guarantee - Customer / Vendor
7111111004 - LC Opened -  Vendor
12511 - IP Land
1131112 - Provision/write off Against Trade Receivables
121 - Investment In Subsidiaries & Other Investments
223 - Deferred Revenue Long Period
31116 - Revaluation Of Fixed Assets (Grp)
414 - Income From Share Trading
51222 - Hotel Operation Cost
6111211 - Rent Expenses (Grp)
1131119001 - Dividend Receivable
1131115037 - Due From-Green United Agricultural Investment
1131115046 - Due from Planet Tax Free
1131115049 - Due from -  Khadem Al Qubaisi
1131115067 - Due from Mohamed Sultan AI Nuaimi Advocates & Legal Consulta
1131313002 - Empower-Chiller Deposit
1131314004 - Deposit- Ministry Of Information
1131215004 - Advances for Investment
1241111001 - Investment In Etisalat Egypt
1231113004 - Citiscape Investment
1261411001 - Fleet
1261456005 - Accudep Vehicle Equipment
1111115001 - Al Hilal Bank
6111911011 - R & M Rentals
6111611004 - Business Promotion
6112211002 - Preoperative License Fee
6111711012 - It Consumables
6111511006 - License Fees
5111112001 - Repair Maintenance
5111116009 - Valet parking Charges
5121911001 - Medical Consumables
5122211001 - Hotel Operation Cost
5121511002 - Fuel Expenses - Projects
6121112002 - Vehicle Loan (Fgb)
6121112006 - Term Loan Interest CBD
2121111010 - Inter-Unit Payable
2121113011 - Due To- East & West
2121113033 - Due to-Citiscape
2121113037 - Due to - Emirates Strategic Investment Company
2121113039 - Due to - Grove Landscaping
2121212007 - Accrued Awards
2121212009 - Accrued Employee Welfare
2121211009 - Accruals Expenses-Food & Catering
4111111001 - Rental Revenue-Tenent
3111711036 - UIRC-Citiscape Adjustment
3111311009 - Hh London Property (Bvi/Savoy)
2211117002 - Sukuk (2024-29)
2211112001 - FAB NBD LOAN
4191311003 - Asset Dispossal Registration Cancellation
1131115072 - Due from EWPD - East West property Development
2141111016 - 2141111016
12711 - Deferred Tax Asset
31115 - Fair Value Reserve
1261412 - Furniture & Fixture
2211211 - Accrued Interest LT,Fgb
2221213 - Pension Payment
5121711 - Design & Consulant Cost
6121112 - Term Loan Interest
1131116004 - Discount against Manazel Receivable
1131314007 - Deposit - MOI - Residency & Foreign Affairs
1131213002 - Prepaid Workmen's Compensation
1131214006 - Employees Account - Furniture Allowance
1221211010 - Unquoted Investment
1221211024 - Provision For Unquoted Invt - Rasmala
1241112002 - Unquoted Impairment overseas invest
1211112002 - Investment In East & West Project 101 Llc
1271111001 - Deferred Tax Asset
1261511001 - PP Work In Progress
1261416002 - Tools & Equipments
1261414004 - Monitor - PC
6111112008 - Medical Insurance
6111113002 - Training Expenses
5121111001 - Basic Salary
6131211016 - Depreciation Laptop
6131211017 - Depreciation IT Equipment
6121113005 - Bank Charges - Others
6121114003 - Tender Fees
2121111014 - Emirates Farms Lap-Consignment Vendor
2121111017 - Gulf Greetings-Consignment Vendor
2121113003 - Due To- Dusit Thani Hotel Ad
2121113008 - Due To- Calibers Industry
2121113052 - Due to Ruya Community Islamic Bank
2121212001 - Accrued Air Ticket Staff
4151111003 - Dog Training Service Corporate - Narcotics
4121311001 - Comprehensive Contract
4121111005 - Laundry Service Revenue
4121611007 - Discount Received
3111711006 - Calibers Contracting
3111311027 - AED STABLECOIN- L.L.C - S.P.C
3111811001 - Prior Period Income/Expense
9999999999 - Opening Balance Control Account
12311 - Invest In Jvs
1251213 - Impairment for IP Buildings
22313 - Retention Accounts payable - long Term
4131111 - Income From Sale Of Properties
5111112 - General Maintenance Cost
5121611 - Machinery & Tools Cost
6 - Gen & Adm Expenses
6111711 -  Office Expenses (Grp)
6111811 - Repair & Maintenance - Building - Offices(Grp)
1131115025 - Due From-Select Market - HO
1131115027 - Due From-Marina Capital
1131116001 - Provision Against Group Company Rec.
1131115029 - Due From-Citiscape
1131115031 - Due From-United Fitche
1131115060 - Due from Sierra Investments LLC
1131213012 - Prepaid Maintenance Expenses
1131213019 - Prepaid Petrol Charges -Rahal Cards
1221211004 - Adnip
1221211005 - Emroc
1221211007 - Provision Against Injaz Mena
1221411005 - Talat Mustafa Group (Prime Securities)
1211112005 - Investment In U G Projects
1251215002 - Machinery (IP)
1141211002 - Provision against Ghantoot Proj -cwip
6111113003 - Visa Expenses New (Direct)
6111611009 - Exhibition & Seminars Exp
6111411006 - Vehicles Salik Expenses
5111116001 - Building Insurance Cost
5122111001 - Workshop Cost
6121112005 - Term Loan Interest Margin
6141111001 - Impairment For IP Land (6-01)
2121111007 - Tenant Payable
2121113020 - Due To- Select Market - DT
2121113038 - Due to Al Reef 2 Al Samha
2121113056 - Due to Aed Stable Coin
2121212008 - Accrued Salaries
3111711018 - Emirates Intl Facility Mngt
3111711019 - Select Market
2231111004 - DEFERED INCOME MARSA DUBAI
2231211001 - Long term Payables
2211119001 - ENBD facility loan
2211111001 - Fgb Bank Loan
2131211002 - Accrued Interest
2141111007 - 2141111007
2141111010 - 2141111010
Gross Profit1 - Gross Profit1
1131119 - Dividend Receivables
1131315 - Maintenance Deposits
12211 - Quoted Local Shares - Long Term
2221112 - LABORS End of Service Benefit
22311 - Deferred Revenue Long Period
3111211 - Statutory Reserves(Grp)
4121112 - Security Guard Revenue
41217 - Taxi Revenue
41913 - Income  From Disposal Of Investment
6111411 - Vehicle Expenses (Grp)
2151111 - Other Provision
12513 - IP WIP
2211116 - SCB loan account
1131117001 - Interest Accrual On Fixed Deposits
1131116003 - Write off Against Group copany Rec.
1131115047 - Due from His Higness account
1131115059 - Due from - Worldwide Canine
1131212001 - Prepaid Medical Insurance
1221211013 - Provision For Unquoted Invt - Al Thuraya
1221211017 - Emaar Industries
1221211019 - National Investment Corporation
1231113001 - Invest In Association
1251215003 - Equipments (IP)
1261112001 - Impairment for PPE Land
1261412001 - Furniture & Fixture
1261455007 - Accudep Softwares
1111118001 - Commercial Bank of Dubai   (CBD)
1111119001 - Dubai Islamic-Bank
6111711014 - Freight & Cargo Expense
6111511008 - Visa Expense - Others
5122411005 - Dog lab Test
5122411007 - Consumable Kitchen tools
6131111002 - Ip Furniture & Fixt, Equipment Depreciation
2121115002 - Advance From Customers
2121211006 - Accruals Expenses-Tenant Charges
4151111004 - Dog Training Service Corporate - Governmental Projects
4111111002 - New Contract Fee
3111711031 - Dusit Thani Legal Reserve
3111311016 - Emirates Hills Service
2111111001 - Fgb OD
11214 - Unquoted Overseas Shares
2121113 - Due To Related Parties
2121115 - Other Payable (Grp)
2121211 - Accruals Expenses
41 - Revenue Sub Group
41221 - Income From Government Contract
413 - Income From Sale Of Properties
51217 - Design & Consulant Cost
51218 - Cost Retails
1111121 - Al Salam Bank
1131115039 - Due From-MotoPro Autoservice
1131115044 - Due from Cititrade Qatar
1131314001 - Ministry Labour Deposit
1131316001 - Abu Dhabi City Municipality (Tawtheeq Dep)
1131213005 - Prepaid Medical Malpractice Insurance
1131213020 - Prepaid - Sukuk Issuance Cost
1131214010 - Employees Account –  Traffic Fine
1221211025 - Aabar Investment
1221411004 - Gulf Real Estate (Maalem)
1231114001 - Prov. Against Invest In Association
1211111013 - Investment In Calibers Industry
1211112008 - Investment In Emirates Africa - Gtii
1231113007 - Citiscape Saudi-Share Of P/L
1261453001 - Accudep Vehicles
1261456002 - Accudep Tools & Equipments
1261456004 - Accudep Machinery
1261458003 - Accudep Medical Instruments
1111120001 - Abu Dhabi Islamic-Bank
6111112003 - Car Allowance
6111112005 - Child Allowance
6111113009 - Out Sourced Manpower
6111211001 - Office Rent
6111511015 - Community Charges
6111711009 - Miscellaneous Expense
6111711021 - Office boys/ cleaners Expenses
5111115003 - Tabreed Expenses
5121911003 - Medical Instruments
5121511013 - Vehicle Maintenance
5121111010 - Food & Catering
4131111001 - Income From Sale Of Properties
4121611003 - OP Clinic - Procedures
4121113002 - Cleaning Income comprehensive
4121114001 - Material Sales Income
4121512008 - Branding
2231111002 - Deferred Revenue Jabel Ali Camp
2211215001 - Accrued Interest LT-SCB
2211111002 - FAB LOAN USD 160M
2141111003 - Deferred Income - Food & Catering
1111123 - Emirates Islamic Bank
1111113 - Other Banks
1131316 - Deposits Others
126 - Property, Plant & Equipments
12612 - Land Advances (Grp)
12614 - PPE Other Assets
22111 - Long Term Loans
22112 - Accrued Interest LT
2221111 - End of Service Benifit
311 - Equity  Group
4121511 - Retail Operation Revenue
41411 - Income From Share Trading
1251311 - IP- WIP
415 - Dog Training Service
1131115010 - Due From-I-Media
1131316003 - Al Sayyah & Sons Investments Llc
1131316006 - Deposit - Suppliers
1131213003 - Prepaid Insurance On Buildings
1131213004 - Prepaid Repairs, Cleaning & Maintenance
1131214005 - Employees Account - Personal Loan  Advance
1221211021 - Capital Investments
1251111001 - IP Land
6111112011 - Remuneration For Board Members
6111212008 - IDA Plus
6111811002 - Other Maintenance Charges
5111114007 - Severage water disposal
5121711002 - Supervision Cost
5121812002 - Rebates
5121511016 - Bank Charges- E payments
5121111004 - Telephone Allowance
6131211003 - Depreciation Furniture & Fixture
6131211011 - Depreciation Medical Equipment
2121113013 - Due To- Fly Zone Payable
4151111001 - Dog Training Service Corporate - Explosive
4121511003 - Arabian Flowers -Consignment Vendor Sales
4121511011 - Green Forest Catering Services & Ready Meals Llc-Consgn_Sale
4111111003 - Renewal Fee
1131215 - Advance To Contractors /Suppliers
1261454 - Accudep Computers & Printers
2121111 - Total Accounts Payable
22312 - Other Non-current Long term liabilities
31112 -  Statutory Reserves (Grp)
3111711 - Share Holder Contribution
41213 - Income from Industry Services
4122111 - Income From Government Contract
5111114 - Building Cleaning Cost
5111115 - Building Utility Cost
5121211 - Material Cost
6111611 -  Business Promotion Expenses
61122 - Preoperative Expenses
1111116 - Standard Chartered Bank
1111117 - Emirates NBD
2211214 - Accrued Interest LT,CBD
61411 - Impairment.
1131115004 - Due From-Deco Design International
1131115015 - Due From-Al Oboor
1131115036 - Due From-Emirates Int'l Facility Management
1131116006 - Provision Against Rabya Qatar Receivable
1131115061 - Due from Yas Pharmaceuticals
1221211006 - Provision For Unquoted Invt - Emroc
1221411006 - Investcorp - Armacell Invt - Euro
1211112004 - Investment In Ug Investments Llc
1211111021 - Investment in TS construction
1251215001 - Furniture & Fixture (IP)
1261451001 - Accudep Fleet
1261414003 - Laptop
1111111001 - First Abu Dhabi Bank
1151111001 - Inventory
6111511001 - Audit Fees
6111711007 - Management Fees
5121611003 - Consumable Materials
5121711003 - Consultant Cost
5121511011 - Misc. Expenses - Projects
5121511012 - Other Project cost
5121112003 - Leave Salary Provisions
2121113048 - Due to Eviqe Diamond
4121111007 - Other Rental Income
4111111006 - Managed Prop Rent Control Account
3111711032 - Citiscape
3111411003 - Southern Sun Retained Earnings
2121111013 - Bakers Crust -Consignment Vendor
11215 - Other Short Term Invest
1131313 - Deposit Against Water & Electricity
1131314 - Ministry Of Labor Deposits
115 - Inventory
1221311 - Quoted Overseas Shares - Long Term
2121114 - Retention Accounts payable - Short term
2211112 - Nbad Bank Loan
4191311 - Income  From Disposal Of Investment
512 - Operation Cost (Grp)
41914 - Income from JV & Associates
6111112 - Other Employees Benefits
12615 - PP WIP
1131218009 - Prepaid Loan Processing Fees - Al Hilal B
1131218011 - Provision For Slow Moving/Expiry Stock - Clinic
1131213017 - Prepaid Pest Control Charges
1131216001 - Prepaid Vehicle Insurance
1221211018 - Gulf Capital
1211111007 - Investment In Arabiya
1211111017 - Investment in Bakers Crust
1251213001 - Impairment for IP Buildings (IP)
1261312001 - Lease Hold Improvement PPE
1261451002 - Accudep Cert Taxi Meter
1141311001 - Development WIP Land
6111112006 - School Allowance
6111611002 - Gifts/Donations
6111411002 - Vehicles Maintenance Expenses
6111311003 - Business Conference & Training
6112211003 - Preoperative Manpower cost
6111711002 - Cleaning Material
6111711013 - Kitchen Expenses
5121611005 - Depreciation vehicles .
5121511009 - Project Manpower
5121111005 - Other Allowance
5121111008 - Child Allowance (UAE National)
5121112001 - Medical Insurance
5121112006 - Pension Expenses
5121113004 - Visa Expenses Others (Direct)
5121113009 - Overtime Expenses- Projects
2121116004 - VAT Prepayment
2121111019 - Roastery House General Trading Llc-Consignment Vendor
2121113010 - Due To- Green Tree Properties
2121212012 - Accrued Expenses - Call Center
2121211008 - Accruals Expenses-Legal Fees
4121311005 - sales of Other Furnitures
4121611004 - Laboratory Sales
3111711008 - East & West
3111711017 - Calibers Contracting-Hh Property Maintenance
3111311018 - HH Al Wathba Stallions
3111411001 - Retained Earnings
2241114001 - Retention Accounts payable
2141111004 - Deferred Income - Laundry Service
3111511 - Fair Value Reserve (Grp)
5122411 - Dog Training Service  Cost
41216 - Healthcare Revenue
41220 - Hotel Operation Revenue
6112211 - Preoperative Expenses
6111113 - Other- Manpower Cost
1111124 - Al Maryah Bank
1131115043 - Due from - Tasameem Construction
1131314006 - Guarantee Deposit - Qatar Airways
1131315001 - Maintenance Deposit
1221211012 - Madain Strategic Investment
1221211002 - East & West Properties
1251212001 - IP Accudep. Buildings
1261416003 - Office Equipment
6111112013 - Leave Encashment - Expenses
6111111003 - Other Allowance
6111411001 - Vehicles Fuel Expenses
6111511018 - Deferred Tax Expense - PL
5121911005 - External Quality
5122011001 - Taxi Operation Cost
5122311001 - Government Contract Cost
5121112009 - Commission
2121113012 - Due To- MotoPro Autoservice
4121211001 - Income from Labour supply
4121111004 - Food & Catering Revenue
4121512006 - Growth Rebates
4111111007 - Short Extension Fee
3111711012 - United Group Holding
3111711034 - Emirates Strategic Investment
2151115003 - Al Aboor Other Provision
4121212002 - Income from Watchman Supply
1221411 - Unquoted Overseas Shares - Long Term
1231114 - Prov. Against Invest In Association
1261414 - Computers & Printers
1261453 - Accudep Vehicles
214 - Deferred Revenue (Grp)
31113 - Owner Current Account
41215 - Retail Operation Revenue
4121611 - Healthcare Revenue
41311 - Income From Sale Of Properties
5121112 - Employee's Other Benefits (Direct)
5121911 - Medical Cost
61113 - Business Travel Expenses
61116 -  Business Promotion Expenses
11413 - Development WIP
2131211 - Accrued-interest
1111125 - Ruya Bank
1131112002 - Write off agnst Trade Receivables
1131115012 - Due From-Al Arabia Press & Media
1131116007 - Provision Against Related Party - Khadem
1131115058 - Due from Turquoise Invt
1131316002 - Arady-Security Deposit
1221211008 - Injaz Mena Investment
1221411001 - Al Shamal Al Janoob Lelzera'A
1211111010 - Investment In Select Market
1211111012 - Investment In Tawasul Autoservices
1211111022 - Investment in Business Capitol Ltd
1211111025 - Investment in Camelia
1261416004 - Machinery PP
6111311002 - Business Hotel Expenses
6111212002 - Internet
6111212006 - Telephone / Fax - Mobile
6111511005 - Taxes
5121113008 - Out Source Manpower cost(dir)
6131211009 - Depreciation Air Craft
6131211014 - Depreciation Automobile
2121111004 - Security Deposit Payable
2121113044 - Due to  - Worldwide Canine
4121112001 - Security Guard Revenue
4121512002 - Rental
3111711026 - Dusit Thani Profit Transfer
3111311015 - Hh Pvt. Affairs Office-Property Maintenance
3111511002 - OCI Change in Fair Value - Corp. Tax
2211120001 - AMCB-loan
2141111001 - Deferred Rental - Building Wise
1121311 - Quoted Overseas Shares
11313 - Deposits
213 - Loans & Advances
3111111 - Share Capital
4121811 - Workshop Taxi Revenue
5131111 - Cos  Of Income From Sale Of Propertied
6111311 - Business  Travel Expenses (Grp)
6121113 - Bank Charges Interest
61311 - Depreciation Ip (Grp)
2121116 - Tax Payable and Settlement
1131112001 - Provision Against Trade Receivables
1131115048 - Due from – Yassat International
1131316009 - Deposit ENBD
1131215001 - Advance To Contractors /Suppliers
1251212002 - Decoration & Renovation (IP)
1261318001 - Medical Equipment
1261413001 - Vehicles
1261456001 - Accudep It - Equipments & Networking
1261454003 - Accudep Laptop
1111121001 - Al-Salam Bank
1111124001 - Al Maryah-Bank
1121211001 - Unquoted-Shares
1151111005 - Project - Inventory for goods received but not invoiced
6111111011 - Cost of Living Allowance (Ind)
6111911009 - Software Support & Maintenance
6111411004 - Vehicles Registration Expenses
6112111002 - Unquoted Impairment
6112011001 - Bad Debts
6111511011 - Haad License Expenses
6111511013 - Company Formation Expense
5111113001 - Security Guard Cost
5121112008 - Awards
6131211012 - Depreciation Vehicle Equipment
6121114001 - Loan Processing Fees
6121111001 - OD Interest Fgb
2121115004 - Others
4121113003 - Material Income
4121114004 - PMU Manpower Income
2231111001 - Deferred Revenue - Mussafah Land Bmtc
2221213001 - Abu Dhabi Retirement Pensions & Benefits Fund
4191311001 - Income  From Disposal Of Investment
4191111006 - Sub Lease Income
6111213004 - Water & Electricity.
1261452002 - Accudep Office Interior Decoration
2141111006 - 2141111006
1111112 - National Bank Abu Dhabi
9999999991 - Test
12611 - PPE- Land
2211111 - Fgb Bank Loan
4121111 - Maintenance Revenue
41214 - Income from Design & Fit outs
4191711 - Exchange Income
5 - Cost
61117 -  Office Expenses
612 - Finance Cost & Interest
61211 - Finance Cost & Interest (Grp)
215 - Other Provision (Grp1)
1131115002 - Due From-United Group Holding
1131115032 - Due From-Rabaya Qatar
1131313003 - Tabreed Deposit
1131213022 - Prepaid - Software & Maintenance
1211112010 - Investment In Emirates Africa
1211111015 - Investment In Yas Healthcare
1211111023 - Investment in 57 tower corp
1231113003 - Rabaya Qatar Investment
1111122001 - Finance  House
1111211001 - Cash On Hand
1121111003 - Quoted Local Shares - Marina Capitol
1121411001 - Unquoted-Overseas Investments
1151111003 - Consignment Inventory
6111111001 - Basic Salary
6111111004 - Special Allowance
6111611003 - Entertainment Expenses
6111611006 - Website Expense
6111711023 - PAR Insurance
5111112002 - Swimming Pool Maintenance
5111114005 - Gift expense
5111116002 - Telephone/Fax/Internet
5111116008 - Landscaping  Cost
5121611002 - Tools & Other Equipment's (Fixed Assets)
5121511014 - Vehicle Salik
6131211001 - Depreciation Building
6121112007 - Term Loan Interest SCB
6141111002 - Impairment for IP Buildings(6-02)
2121112001 - Notes Payable
2121113001 - Due To- Das Holding Llc
2121211007 - Purchase Expenditure, un-invoiced
4121611001 - Out-Patient/Clinic Sales - Direct
4121511006 - Fresh Fishing Fish Td-Consignment Vendor Sales
4121511013 - Consignment Sales
4121512004 - Registration & Listing Fee
3111711020 - United Group Holding - Municipality Proj.
1251112 - Impairment for IP Land
4121212 - Income from Watchman Supply
1141111 - Contract Work In Progress
12411 - Other Investment Long Term
22211 - End of Service Benifit
5122311 - Government Contract Cost
1131214 - Employees Account ( Grp)
1131115019 - Due From-Manazel Real Estate
1131115040 - Due From-Tasameem Real Estate
1131218006 - Prepaid Expenses
1131213007 - Prepaid Medical Equipment
1211111019 - Investment in UDI
1261314001 - Accum. Dep Leasehold Improvement
1261417001 - Embraer Air Craft
1111113001 - Other Banks
6111911002 - R & M Printers
6111311004 - Business Travel Ticket
5111114004 - Pest Control
5131111002 - Vehicle Insurance
5121511004 - Vehicle Registration
6131211006 - Depreciation  Equipment's
6131211018 - Depreciation Monitor PC
6121113004 - Portfolio Commission Expenses
2121115003 - PDC Payable
2121116006 - Corporate Tax Asset/Liability
2121111005 - Authority Charges Payable
2121111026 - Tabarak Investment
2121113026 - Due To- Southern Sun Hotel Abu Dhabi
2121211005 - Accruals Expenses-Telephone/Fax/mobile/Internet
4151111002 - Dog Training Service Corporate - Patrol
4111111004 - Cancellation Charges
3111711039 - Citiscape Dubai Branch
3111311020 - HH Al Wathba Farm AD
2211116001 - SCB-loan account
4191312001 - Asset Disposal Vehicle
4191111007 - Provision for Write Back
2121116002 - VAT Settlement
6111811006 - 6111811006
Gross Profit - Gross Profit
111 - Cash & Cash Equivalents
1211111 - Investment In Subsidiaries
1261411 - Fleet
1261418 - Equipment Medical
31117 - Share Holder Contribution
4121113 - Cleaning Services
51214 - Rent Expenses (Direct)
1141311 - Development-WIP
6121116 - Finanace Cost Sukuk
1131115003 - Due From-Das Holding L.L.C
1131115013 - Due From-Green Tree Property Management
1131115022 - Due From-Select Market - DT
1131115063 - Due from Eviqe Diamond
1131115070 - Due from EAST & WEST PROPERTIES 2 SPV LIMITED
1131312001 - Landlord Deposit - Office
1231113002 - Investment In Manazel Shares
1211111016 - Share Capital- East & West Tourism LLC(S.S.Hotel)
6111112012 - Incentive
6111911007 - R & M Medical Equipments
6111213003 - Cooling charges
6111711015 - Fidelity Insurance
5111115004 - COOLING CHARGE
5111111002 - Facility Managment Charges
5121311003 - Sub Contract Cost - Projects
5121812003 - Loyalty
5121812004 - Rounding Account
5121511008 - Accommodation Exp
5121111002 - House Rent Allowance
2121112002 - Provision for Supplier Invoices
2121113046 - Due to Yas Pharmaceuticals
2121113051 - Due to East & West Properties
2121212002 - Accrued Air Ticket Labour
2121212004 - Accrued Leave Salary Salary
4121411002 - Income from Design
4121711001 - Taxi Operating Revenue
4121511010 - Roastery House General Trading Llc-Consignment Vendor Sales
4121512003 - Excess/Shortage
3111711004 - Calibers Recruitment - FT
3111711010 - I - Media
2141112003 - Min. Of Presidential Affairs (Def. Rev.)
2111112001 - Adcb OD
12213 - Quoted Overseas Shares - Long Term
1231111 - Invest In Jvs
1261416 - Office Equipment's
2211113 - Adcb Bank Loan
51212 - Material Cost
51220 - Taxi Operation Cost
6112011 -  Provision For Bad Debts (Grp)
2211115 - Margin Trading Account
2211118 - CBD-loan account
4151111 - Dog  Training Service
1131111001 - Trade Receivables
1131111003 - Receivable from Tenant
1131120003 - PDC Receivable
1221411003 - Starfield Growth
1251216002 - Accudep. Machinery (IP)
1231113006 - Citiscape Investment-Share Of P/L
1261315001 - Impairment for Buildings (PP)
1261358001 - Accudep Medical Equipment
1151111004 - Inventory for goods issued but not invoiced
6111113005 - Visa Expenses Others (Direct)
6111311001 - Business Travel Allowance
6111811004 - Leasehold Improvement Amortization
6111213002 - Water Charges
6111212005 - Mpls Link
5111115001 - Electricity Expenses
5121812001 - Commercial Discount
5121113007 - Training Expenses (Dir)
6121113002 - Lg Charges
6121113006 - Foreign Exchange Variation
2121111006 - Gift Card Reedemable Accounts
2121113016 - Due To- Emirates International Facility Managemen
2121113023 - Due To- Select Market - HO
2121212011 - Accrued Pension - UGH
2121211002 - Accrued Payable for Goods Received but not Invoiced
2121211011 - Accruals Expenses – Service charges
4121411001 - Income from Design & Fit outs
4121512010 - Listing Fee
4121512014 - Cost Reduction
3111711022 - Dusit Thani Ad
4191211001 - Dividend
4141211001 - Portfolio Valuation Gain / Loss
1111123001 - Emirates Islamic Bank-EIB
123 - Invest In Jvs & Association
1231113 - Invest In Association
1261451 - Accudep Fleet
21212 - Accruals
221 - Term Loans
2211212 - Accrued Interest LT,Adcb
31118 - Prior Period Adjustment
3111811 - Prior Period Adjustment
4 - Revenue Main Group
51215 - Other Direct Cost
6131211 - Depreciation For Pp (Grp)
21511 - Other Provision (Grp2)
1111111 - First Gulf  Bank
1111122 - Finance House
71111 - Off Balance Sheet Items..

## GL hierarchy matching rule

When the user mentions an account/finance term, resolve it from higher to lower hierarchy and choose only one best-fit level for filtering.

Mandatory search order:

1. Search candidate match at `L1`.
2. Then refine at `L2` if available in the tree/content.
3. Then refine at `L3`.
4. Then refine at `L5`.
5. Then refine at `L7`.

Selection rule:

1. Pick the single most apt node based on user wording and intent.
2. Do not apply multiple unrelated hierarchy levels in the same filter unless explicitly requested.
3. If a precise child term exists, prefer that child over a broad parent.
4. If only a broad parent is mentioned, keep parent-level filter.
5. If user asks for "breakdown" without naming a specific non-hierarchy dimension, use next hierarchy level as grouping dimension (L1->L2, L2->L3, L3->L5, L5->L7).
6. If user explicitly names a breakdown dimension (e.g., month/year/community/project), that explicit dimension overrides the hierarchy-breakdown default.

SQL filter rule after selection:

1. If selected node is `L7`, filter exact `a.\[mainaccounthierarchy-1\_L7]`.
2. If selected node is `L5`, filter `a.\[mainaccounthierarchy-1\_L5]` (covers L7 children).
3. If selected node is `L3`, filter `a.\[mainaccounthierarchy-1\_L3]` (covers L5/L7 children).
4. If selected node is `L2`, filter `a.\[mainaccounthierarchy-1\_L2]` or `a.\[mainaccounthierarchy-1\_L2-Name]` if present.
5. If selected node is `L1`, filter `a.\[mainaccounthierarchy-1\_L1]` or `a.\[mainaccounthierarchy-1\_L1-Name]`.

Example:

* User asks `Rental Revenue`: match L7 `4111111 | Rental Revenue`, so filter:

```sql
a.\[mainaccounthierarchy-1\_L7] = '4111111'
```

* User asks `Rental Revenue Group`: match L3 `411 | Rental Revenue (Grp)` or L5 `41111 | Rental Revenue (Grp)` depending on wording.
* User asks `Revenue`: broad L1 revenue. Use:

```sql
a.\[mainaccounthierarchy-1\_L1-Name] = 'Revenue Main Group'
```

or:

```sql
a.\[mainaccounthierarchy-1\_L1] = '4'
```

For the confirmed total revenue report, the working filter is:

```sql
a.\[mainaccounthierarchy-1\_L1-Name] = 'Revenue Main Group'
```

\---

# Payables State Transactions rules

`PayablesStateTransactions` is a state/snapshot fact table used for payables balance, average payables, before-due payables, overdue/after-due payables, and payable aging-style KPIs.

Use this table for questions such as:

- Payables Balance
- Average Payables
- Payables Before Due
- Payables Overdue
- Payables After Due
- % Payables Overdue
- Payables due-status breakdown
- Payables due analysis by buckets (Due Overdue / `da.DueDays` — see [Payables DueDays bucket rule](#payables-duedays-bucket-rule))

## Important columns

| Column | Meaning / SQL usage |
|---|---|
| `DateID` | Date key in `YYYYMMDD` format. |
| `PayablesBalance` | Payables closing balance amount. Use for Payables Balance. |
| `hPayablesBalanceSum` | Payables balance amount used in before-due/overdue/average payables measures. |
| `DueAnalysisID` | Join key to `DueAnalysis` table. |
| `DueDays` | **On `DueAnalysis`** (use as `da.DueDays` after `INNER JOIN DueAnalysis da ON p.DueAnalysisID = da.DueAnalysisID`). For due-bucket breakdowns, classify **only** with `da.DueDays` (see [Payables DueDays bucket rule](#payables-duedays-bucket-rule)); do not use `Group1`–`Group3` or group description columns for bucket logic. |
| `FDCommunityID` | Join to `Community` for EWIG/GTPM/TRE filtering. |

## Default joins

```sql
FROM PayablesStateTransactions p
INNER JOIN Community cm
    ON p.FDCommunityID = cm.FinancialDimension4ID
```

For due-status measures, also join `DueAnalysis`:

```sql
INNER JOIN DueAnalysis da
    ON p.DueAnalysisID = da.DueAnalysisID
```

If the physical table is named `[Due Analysis]`, use:

```sql
INNER JOIN [Due Analysis] da
    ON p.DueAnalysisID = da.DueAnalysisID
```

## Payables Balance rule

Payables Balance is a state/snapshot measure.

Do not sum Payables Balance across the full date range.

Use the latest `DateID` in the selected period.

DAX pattern:

```dax
CALCULATE(
    SUM([Payables Balance]),
    LASTDATE('Date'[Date])
)
```

SQL pattern:

```sql
WITH LatestDate AS (
    SELECT
        MAX(p.DateID) AS LatestDateID
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND p.DateID BETWEEN <StartDateID> AND <EndDateID>
)
SELECT
    SUM(p.PayablesBalance) AS PayablesBalance
FROM PayablesStateTransactions p
INNER JOIN Community cm
    ON p.FDCommunityID = cm.FinancialDimension4ID
INNER JOIN LatestDate ld
    ON p.DateID = ld.LatestDateID
WHERE cm.Code = 'EWIG';
```

### Payables Balance by quarter (or by calendar grain)

`PayablesBalance` is a **closing snapshot** per `DateID`. **Wrong:** `SUM(PayablesBalance)` over every `DateID` in a quarter — that stacks many closing balances and **inflates** the number. **Right:** for each quarter (or month / year), take the **latest `DateID` inside that grain**, then sum `PayablesBalance` **only** for rows on that date (one closing snapshot per quarter).

**Rule:** Payables Balance by quarter = balance on the **latest available date of each quarter**, not the sum of balances across all dates in the quarter.

SQL pattern (calendar quarter from integer `DateID` `YYYYMMDD`; use `<StartDateID>` / `<EndDateID>` for the window):

```sql
WITH Base AS (
    SELECT
        p.DateID,
        p.PayablesBalance,
        p.DateID / 10000 AS [Year],
        (((p.DateID / 100) % 100) + 2) / 3 AS [Quarter]
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND p.DateID BETWEEN <StartDateID> AND <EndDateID>
),
LatestQuarterDate AS (
    SELECT
        [Year],
        [Quarter],
        MAX(DateID) AS LatestDateID
    FROM Base
    GROUP BY
        [Year],
        [Quarter]
)
SELECT
    b.[Year],
    b.[Quarter],
    l.LatestDateID,
    CAST(
        ROUND(SUM(b.PayablesBalance) / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS PayablesBalance_Mn
FROM Base b
INNER JOIN LatestQuarterDate l
    ON b.[Year] = l.[Year]
   AND b.[Quarter] = l.[Quarter]
   AND b.DateID = l.LatestDateID
GROUP BY
    b.[Year],
    b.[Quarter],
    l.LatestDateID
ORDER BY
    b.[Year],
    b.[Quarter];
```

For **month** or **year** snapshots, use the same idea: `MAX(DateID)` per month (or year), then join back and sum `PayablesBalance` on that date only.

## Average Payables rule

Average Payables is the average of daily payables balances across the selected period.

Do not use latest-date logic for Average Payables.

First calculate daily payables balance by `DateID`, then average those daily balances.

SQL pattern:

```sql
WITH DailyPayables AS (
    SELECT
        p.DateID,
        SUM(p.hPayablesBalanceSum) AS DailyPayablesBalance
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND p.DateID BETWEEN <StartDateID> AND <EndDateID>
    GROUP BY
        p.DateID
)
SELECT
    AVG(CAST(DailyPayablesBalance AS DECIMAL(38,10))) AS AveragePayables
FROM DailyPayables;
```

### Average Payables by quarter (or by grain)

**Different from Payables Balance by quarter:** Average Payables is **not** the closing balance on the last day of the quarter. First build **daily** balance (`SUM(hPayablesBalanceSum)` per `DateID`), then **average** those daily values **within each quarter** (group by year/quarter derived from `DateID`, then `AVG(DailyPayablesBalance)` per group). Do not use latest-`DateID`-only logic for averages.

## Due Analysis Group1 rule for Payables

For Payables State Transactions due-status measures:

- `DueAnalysis.Group1 = -1` means Before Due
- `DueAnalysis.Group1 = 1` means Overdue / After Due

Use this only for Payables due-status measures.

### Payables Before Due

Use latest selected date and filter `da.Group1 = -1`.

SQL expression:

```sql
SUM(CASE
        WHEN da.Group1 = -1
        THEN p.hPayablesBalanceSum
        ELSE 0
    END) AS PayablesBeforeDue
```

### Payables Overdue / After Due

Use latest selected date and filter `da.Group1 = 1`.

SQL expression:

```sql
SUM(CASE
        WHEN da.Group1 = 1
        THEN p.hPayablesBalanceSum
        ELSE 0
    END) AS PayablesOverdue
```

## % Payables Overdue rule

`% Payables Overdue = Payables Overdue / Payables Balance`

SQL pattern:

```sql
CASE
    WHEN PayablesBalance IS NULL OR PayablesBalance = 0 THEN NULL
    ELSE (PayablesOverdue * 100.0) / PayablesBalance
END
```

## Standard Payables Balance + Before Due + Overdue pattern

```sql
WITH LatestDate AS (
    SELECT
        MAX(p.DateID) AS LatestDateID
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND p.DateID BETWEEN <StartDateID> AND <EndDateID>
),
agg AS (
    SELECT
        SUM(p.PayablesBalance) AS PayablesBalance,

        SUM(CASE
                WHEN da.Group1 = -1
                THEN p.hPayablesBalanceSum
                ELSE 0
            END) AS PayablesBeforeDue,

        SUM(CASE
                WHEN da.Group1 = 1
                THEN p.hPayablesBalanceSum
                ELSE 0
            END) AS PayablesOverdue
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    INNER JOIN LatestDate ld
        ON p.DateID = ld.LatestDateID
    INNER JOIN DueAnalysis da
        ON p.DueAnalysisID = da.DueAnalysisID
    WHERE cm.Code = 'EWIG'
)
SELECT
    CAST(ROUND(PayablesBalance / 1000000.0, 4) AS DECIMAL(18,4)) AS PayablesBalance_Mn,
    CAST(ROUND(PayablesBeforeDue / 1000000.0, 4) AS DECIMAL(18,4)) AS PayablesBeforeDue_Mn,
    CAST(ROUND(PayablesOverdue / 1000000.0, 4) AS DECIMAL(18,4)) AS PayablesOverdue_Mn,
    CAST(
        ROUND(
            CASE
                WHEN PayablesBalance IS NULL OR PayablesBalance = 0 THEN NULL
                ELSE (PayablesOverdue * 100.0) / PayablesBalance
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS PayablesOverduePercent
FROM agg;
```

## Payables DueDays bucket rule

**Scope:** This is **payables** (accounts payable / AP) due analysis on `PayablesStateTransactions` + `DueAnalysis` — not generic “due analysis” (other domains, e.g. receivables, use different tables and rules).

When the user asks for **payables due analysis by buckets** (aging / overdue / Due Overdue–style buckets on payables), use **`DueAnalysis.DueDays`** only (in SQL: `da.DueDays` with `INNER JOIN DueAnalysis da ON p.DueAnalysisID = da.DueAnalysisID`). Do not use `PayablesStateTransactions.DueDays` for bucket CASE logic when `DueDays` is defined on `DueAnalysis`.

Do not use `Group1`, `Group2`, `Group3`, `Group1Desc`, `Group2Desc`, or `Group3Desc` for bucket logic for now.

Use `da.DueDays` to classify before-due and overdue buckets.

### Payables due analysis presentation format (Due Overdue buckets)

When the user asks for **payables due analysis by buckets** (AP aging / overdue breakdown), shape the answer like the **Due Overdue** hierarchy: use the **exact** `DueBucket` strings below, this **order**, and end with a **Total** row (sum of all bucket amounts). If the question only says “due analysis” without payables/AP context, confirm they mean **payables** before using this layout.

1. **Due Overdue** — use as the report / section title (plain text or heading in the answer, not a SQL column unless you add one).
2. **Before due** — list child buckets in this order (matches standard Due Overdue report; descending range under Before due):
   - `Before due 61 - 90 days`
   - `Before due 31 - 60 days`
   - `Before due under 30 days`
   - If the data includes **Before due over 90 days** (`da.DueDays <= -91`), show it **above** `Before due 61 - 90 days` (same parent, first child when present).
3. **Overdue** — list child buckets in this order (ascending aging):
   - `Overdue under 30 days`
   - `Overdue 31 - 60 days`
   - `Overdue 61 - 90 days`
   - `Overdue 91 - 120 days`
   - `Overdue 121 - 150 days`
   - `Overdue 151 - 180 days`
   - `Overdue 181 - 365 days`
   - `Overdue 1 - 2 years`
   - `Overdue 2 years`
4. **Total** — one line: label `Total` and amount = sum of all bucket amounts (the reference SQL adds this row with `UNION ALL`; use millions formatting in the outer projection if the user asks for amounts in millions).

Do not rename buckets (spacing, hyphens, wording) for **payables** due-by-bucket answers. The final overdue bucket label is **`Overdue 2 years`** (not “over 2 years”).

Assumption and bucket mapping:

```text
DueAnalysis.DueDays <= 0  = Before due
DueAnalysis.DueDays > 0   = Overdue / After due

DueDays <= -91        → Before due over 90 days
DueDays -90 to -61    → Before due 61 - 90 days
DueDays -60 to -31    → Before due 31 - 60 days
DueDays -30 to 0      → Before due under 30 days

DueDays 1 to 30       → Overdue under 30 days
DueDays 31 to 60      → Overdue 31 - 60 days
DueDays 61 to 90      → Overdue 61 - 90 days
DueDays 91 to 120     → Overdue 91 - 120 days
DueDays 121 to 150    → Overdue 121 - 150 days
DueDays 151 to 180    → Overdue 151 - 180 days
DueDays 181 to 365    → Overdue 181 - 365 days
DueDays 366 to 730    → Overdue 1 - 2 years
DueDays >= 731        → Overdue 2 years
```

Important boundary rule (values read from `da.DueDays`):

- `da.DueDays = 90` → Overdue 61 - 90 days
- `da.DueDays = 91` → Overdue 91 - 120 days
- `da.DueDays = 60` → Overdue 31 - 60 days
- `da.DueDays = 61` → Overdue 61 - 90 days

### Payables due bucket SQL pattern

`PayablesStateTransactions` is a snapshot/state table. **`DueDays` for bucketing comes from `DueAnalysis`** (`da.DueDays`).

For **payables** due analysis by buckets, use the latest `DateID` in the selected period. Do not sum across the full date range. If the physical table is `[Due Analysis]`, substitute that name for `DueAnalysis` in the join.

Amounts below are in **native currency** with two decimals; for **millions** output like other payables examples, wrap `PayablesAmount` in `CAST(ROUND(... / 1000000.0, 4) AS DECIMAL(18,4))` and use a `_Mn` column alias.

```sql
WITH LatestDate AS (
    SELECT
        MAX(p.DateID) AS LatestDateID
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND p.DateID BETWEEN <StartDateID> AND <EndDateID>
),
bucketed AS (
    SELECT
        CASE
            WHEN da.DueDays <= -91 THEN 'Before due over 90 days'
            WHEN da.DueDays BETWEEN -90 AND -61 THEN 'Before due 61 - 90 days'
            WHEN da.DueDays BETWEEN -60 AND -31 THEN 'Before due 31 - 60 days'
            WHEN da.DueDays BETWEEN -30 AND 0 THEN 'Before due under 30 days'
            WHEN da.DueDays BETWEEN 1 AND 30 THEN 'Overdue under 30 days'
            WHEN da.DueDays BETWEEN 31 AND 60 THEN 'Overdue 31 - 60 days'
            WHEN da.DueDays BETWEEN 61 AND 90 THEN 'Overdue 61 - 90 days'
            WHEN da.DueDays BETWEEN 91 AND 120 THEN 'Overdue 91 - 120 days'
            WHEN da.DueDays BETWEEN 121 AND 150 THEN 'Overdue 121 - 150 days'
            WHEN da.DueDays BETWEEN 151 AND 180 THEN 'Overdue 151 - 180 days'
            WHEN da.DueDays BETWEEN 181 AND 365 THEN 'Overdue 181 - 365 days'
            WHEN da.DueDays BETWEEN 366 AND 730 THEN 'Overdue 1 - 2 years'
            WHEN da.DueDays >= 731 THEN 'Overdue 2 years'
        END AS DueBucket,

        CASE
            WHEN da.DueDays <= 0 THEN 'Before due'
            WHEN da.DueDays > 0 THEN 'Overdue'
        END AS DueStatus,

        p.hPayablesBalanceSum AS PayablesAmount
    FROM PayablesStateTransactions p
    INNER JOIN Community cm
        ON p.FDCommunityID = cm.FinancialDimension4ID
    INNER JOIN LatestDate ld
        ON p.DateID = ld.LatestDateID
    INNER JOIN DueAnalysis da
        ON p.DueAnalysisID = da.DueAnalysisID
    WHERE cm.Code = 'EWIG'
),
agg AS (
    SELECT
        DueStatus,
        DueBucket,
        SUM(PayablesAmount) AS PayablesAmount
    FROM bucketed
    WHERE DueBucket IS NOT NULL
    GROUP BY
        DueStatus,
        DueBucket
),
final_rows AS (
    SELECT
        DueStatus,
        DueBucket,
        CAST(ROUND(PayablesAmount, 2) AS DECIMAL(18,2)) AS PayablesAmount,
        CASE
            WHEN DueBucket = 'Before due over 90 days' THEN 1
            WHEN DueBucket = 'Before due 61 - 90 days' THEN 2
            WHEN DueBucket = 'Before due 31 - 60 days' THEN 3
            WHEN DueBucket = 'Before due under 30 days' THEN 4
            WHEN DueBucket = 'Overdue under 30 days' THEN 5
            WHEN DueBucket = 'Overdue 31 - 60 days' THEN 6
            WHEN DueBucket = 'Overdue 61 - 90 days' THEN 7
            WHEN DueBucket = 'Overdue 91 - 120 days' THEN 8
            WHEN DueBucket = 'Overdue 121 - 150 days' THEN 9
            WHEN DueBucket = 'Overdue 151 - 180 days' THEN 10
            WHEN DueBucket = 'Overdue 181 - 365 days' THEN 11
            WHEN DueBucket = 'Overdue 1 - 2 years' THEN 12
            WHEN DueBucket = 'Overdue 2 years' THEN 13
        END AS SortKey
    FROM agg

    UNION ALL

    SELECT
        NULL AS DueStatus,
        'Total' AS DueBucket,
        CAST(ROUND(SUM(PayablesAmount), 2) AS DECIMAL(18,2)) AS PayablesAmount,
        99 AS SortKey
    FROM agg
)
SELECT
    DueStatus,
    DueBucket,
    PayablesAmount
FROM final_rows
ORDER BY
    SortKey;
```

Mistakes to avoid (DueDays buckets):

- Do not use `Group1`, `Group2`, or `Group3` for bucket logic for now.
- Do not sum payables state rows across the full date range for **payables** due-by-bucket analysis; always use the latest `DateID` in the selected period.
- Use **`da.DueDays`** from **`DueAnalysis`** for bucket CASE expressions; do not use `p.DueDays` when `DueDays` is a column on `DueAnalysis`.
- Use `da.DueDays` bucket boundaries exactly.
- Do not put `da.DueDays = 90` into 91 - 120; it belongs to 61 - 90.

## Payables vendor key rule (denormalized)

`PayablesStateTransactions` and `PayablesTransactions` expose vendor identifiers directly. **Do not** join the `Vendor` dimension just to read a name, and **do not** use `FDVendorID` as the default vendor key.

### Pay-to vendor columns (default)

Use **Pay-to** for all default vendor reporting on payables.

| Column | Use |
|---|---|
| `PayToVendorID` | Default vendor key for `JOIN` / `GROUP BY` |
| `PayToVendorName` | Display name (wrap with `MAX(...)` when grouping by `PayToVendorID`) |
| `PayToVendorCountry` | Pay-to vendor country |
| `PayToVendorStateCode` | Pay-to vendor state code |
| `PayToVendorGroup` | Pay-to vendor group |

Default key for:

- Top vendors by Payables Balance
- Payables Overdue by vendor
- % Payables Overdue by vendor
- Payables Overdue Days by vendor
- Payables Turnover Days by vendor
- Vendor Purchase on Credit by vendor (physical column: **`VendorPurchaseonCredit`** on `PayablesTransactions` — see [Vendor Purchase on Credit physical column rule](#vendor-purchase-on-credit-physical-column-rule))
- Vendor Net Change by vendor

Reason: `PayToVendorID` is the payment-party (who you owe / pay). `FDVendorID` is an analytical financial-dimension key — do **not** default to it.

### Vendor Purchase on Credit physical column rule

The DAX / semantic measure name is **`Vendor Purchase on Credit`** (with spaces). The **physical SQL column** on `PayablesTransactions` is:

```sql
VendorPurchaseonCredit   /* no spaces, lowercase 'on' */
```

Use this exact name. **Do not** write:

- `[Vendor Purchase on Credit]` (bracketed semantic name — that is not a SQL column)
- `VendorPurchaseOnCredit` (camelCase `On` is wrong; it is lowercase `on`)
- `Payables Transactions_Vendor Purchase on Credit` (semantic table-prefixed name)

Confirmed pattern:

```sql
SUM(pt.VendorPurchaseonCredit) AS VendorPurchaseOnCredit
FROM PayablesTransactions pt
```

### Buy-from vendor columns (only on explicit request)

| Column | Use |
|---|---|
| `BuyFromVendorID` | Buy-from vendor key |
| `BuyFromVendorName` | Buy-from display name |
| `BBuyFromVendorCountry` | Buy-from vendor country (**double `B`** in `PayablesStateTransactions` — confirm physical name) |
| `BuyFromVendorStateCode` | Buy-from state code |
| `BuyFromVendorGroup` | Buy-from group |

Use these **only** when the user explicitly asks for buy-from / supplier-source analysis.

### Payables state ↔ transaction join rule

When combining `PayablesStateTransactions` (`p`) and `PayablesTransactions` (`pt`), join on:

```sql
p.PayToVendorID = pt.PayToVendorID
```

Display:

```sql
MAX(p.PayToVendorName)  AS PayToVendorName
/* or */
MAX(pt.PayToVendorName) AS PayToVendorName
```

## Mistakes to avoid (Payables State Transactions)

- Do not sum `PayablesBalance` across the full date range for Payables Balance.
- For Payables Balance, always use the latest `DateID` in the selected period.
- For **quarter-wise (or month-wise) Payables Balance**, do not `SUM(PayablesBalance)` over every date in the grain; use **latest `DateID` per quarter/month** then sum only those rows.
- Do not confuse Payables Balance with Average Payables.
- Payables Balance = closing balance at latest selected date (per period grain when reporting by quarter/month).
- Average Payables = average of **daily** balances across the selected period; by quarter, average daily balances **within** each quarter — not the quarter-end snapshot.
- Do not calculate Payables Before Due or Payables Overdue without joining `DueAnalysis`.
- For Payables Before Due, use `Group1 = -1`.
- For Payables Overdue / After Due, use `Group1 = 1`.

\---

# 3\. Community dimension: `Community`

Use `Community` for community/portfolio filters such as EWIG, GTPM, TRE, EWP, etc.

## Join

```sql
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
```

## Important columns

|Column|Meaning|
|-|-|
|`FinancialDimension4ID`|Primary key. Join from `GLTransactions.FDCommunityID`.|
|`Code`|Community code. Preferred filter field. Example: `EWIG`.|
|`Name`|Community name.|
|`DimensionCode`|Usually `Community`. Not required if `Code` filter is enough.|

## Confirmed EWIG rule

For the confirmed EWIG revenue report, use:

```sql
cm.Code = 'EWIG'
```

Default behavior for all community-scoped queries:

```sql
cm.Code = 'EWIG'
```

Only override the above when the user explicitly specifies a different community code/name.

Do not use company, ledger, or project for this confirmed EWIG revenue logic.

## Denormalized location columns on facts

The following display columns are available **directly** on payables, receivables, sales, misc-charge, and GL facts (`PayablesStateTransactions`, `PayablesTransactions`, `ReceivablesStateTransactions`, `ReceivablesTransactions`, `ReceivablesDueAnalysis`, `SalesInvoiceTransactions`, `SalesInvoiceMiscChargesTransactions`, `GLTransactions`):

| Column | Use |
|---|---|
| `BuildingName` | Building display / `GROUP BY` |
| `UnitName` | Unit display / `GROUP BY` on `GLTransactions` (leasing/rental revenue) |
| `CommunityName` | Community display / `GROUP BY` |
| `LocationName` | Location display / `GROUP BY` (on GL: only when user asks for location) |
| `RegionName` | Region display / `GROUP BY` on `GLTransactions` (only when user asks for region) |

For rental revenue, occupancy, and lease routing, see **[Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules)**.

Use these columns directly for **display** and **`GROUP BY`** — no extra `Building` / `Location` dimension join needed for the name.

**Filtering EWIG:** prefer the existing **`Community`** join + **`cm.Code = 'EWIG'`** when a join is already in the query (still the single source of truth for community filtering):

```sql
INNER JOIN Community cm
    ON <fact>.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
```

Fallback when no `Community` join is used and the exact display name is known:

```sql
WHERE CommunityName = '<exact community name>'
```

\---

# 4\. Company dimension: `dimCompany`

Use only when the question asks for company/legal entity.

## Join

```sql
INNER JOIN dimCompany c
    ON t.CompanyID = c.CompanyID
```

## Important columns

|Column|Meaning|
|-|-|
|`CompanyID`|Company key.|
|`CompanyCode`|Company code, e.g. `EWIG`.|
|`CompanyName`|Company name.|

Known value:

```text
CompanyID = 4
CompanyCode = EWIG
CompanyName = East \& West International Group
```

\---

# 5\. Ledger dimension: `GLLedger`

Use only when the question asks for ledger.

## Join

```sql
INNER JOIN GLLedger l
    ON t.GLLedgerID = l.GLLedgerDimPKID
```

## Important columns

|Column|Meaning|
|-|-|
|`GLLedgerDimPKID`|Ledger primary key.|
|`LEDGER\_NAME`|Ledger code, e.g. `EWIG`.|
|`LEDGER\_DESCRIPTION`|Ledger full description.|
|`LEDGER\_ACCOUNTINGCURRENCY`|Accounting currency, e.g. `AED`.|

Known value:

```text
GLLedgerDimPKID = 4
LEDGER\_NAME = EWIG
LEDGER\_DESCRIPTION = East \& West International Group
```

\---

# 6\. Project dimension: `Project`

Use only when the question asks for project-level analysis.

## Join

```sql
INNER JOIN Project p
    ON t.FDProjectID = p.FinancialDimension23ID
```

## Important columns

|Column|Meaning|
|-|-|
|`FinancialDimension23ID`|Project primary key.|
|`Code`|Project code.|
|`Name`|Project name.|
|`DimensionCode`|Usually `Project`.|

Do not assume EWIG means project unless explicitly stated.

\---

# 7\. Calculation rules

## Revenue

Use:

```sql
-SUM(t.GLNetChangeACY)
```

Reason: revenue is credit-side, so the business reporting value should be shown as positive.

Revenue account filter:

```sql
a.\[mainaccounthierarchy-1\_L1-Name] = 'Revenue Main Group'
```

Revenue in millions (default):

```sql
(-SUM(t.GLNetChangeACY)) / 1000000.0
```

## Cost, expense, and other GL amounts (non-revenue)

For **cost**, **expense**, **asset**, **liability**, **equity**, and other **non-revenue** GL filters, use the **normal** aggregate sign — **`SUM(t.GLNetChangeACY)`** — **not** `-SUM`. Apply the same millions wrapper as for revenue:

```sql
CAST(ROUND(SUM(t.GLNetChangeACY) / 1000000.0, 4) AS DECIMAL(18,4))
```

Only **revenue** uses negation on `GLNetChangeACY` so business-facing revenue reads positive.

Clean decimal output:

```sql
CAST(ROUND(<expression>, 4) AS DECIMAL(18,4))
```

Chart-style decimal output:

```sql
CAST(ROUND(<expression>, 2) AS DECIMAL(18,2))
```

## Total Expenses rule

Use this rule whenever the user asks for **total expenses** / **overall expenses** / **total cost and expenses** / **expense total** for a period, or **expenses YTD / MTD / variance** without naming a specific expense category.

### Confirmed logic

**Total Expenses** rolls up two **L1** hierarchy buckets:

```text
Total Expenses = Cost + Gen & Adm Expenses
```

Filter:

```sql
a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')
```

Amount:

```sql
SUM(t.GLNetChangeACY)
```

**Do not** use `-SUM(t.GLNetChangeACY)` for total expenses. The unary minus is **revenue-only**; cost / expense / total-expense rollups use **raw `SUM`**.

### Standard SQL pattern

```sql
SELECT
    CAST(
        ROUND(SUM(t.GLNetChangeACY) / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS TotalExpenses_Mn
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
  AND a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')
  AND t.DateID BETWEEN <StartDateID> AND <EndDateID>;
```

### Example: Total Expenses for 2024

```sql
SELECT
    CAST(
        ROUND(SUM(t.GLNetChangeACY) / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS TotalExpenses_2024_Mn
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
  AND a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')
  AND t.DateID BETWEEN 20240101 AND 20241231;
```

Apply standard time-intelligence (YTD / MTD / variance / rolling) on top of this base by replacing `<StartDateID>` / `<EndDateID>` only — do **not** swap the `L1-Name IN (...)` filter for one of the children unless the user explicitly asks for just `Cost` or just `Gen & Adm Expenses`.

## Debit / credit

Use only if specifically requested:

```sql
SUM(t.GLDebitACY)
SUM(t.GLCreditACY)
```

## Sales / Net Sales

**Do not conflate “net sales” with GL revenue.**  
- **Net sales** (user says *net sales*, *invoice net sales*, *sales after discount*, sell-to / sales subledger): use **`SalesInvoiceTransactions`** + **`SalesInvoiceMiscChargesTransactions`** only — **never** `GLTransactions` or **`Revenue Main Group` / L1–L7** for the total.  
- **Revenue** (P&L, *rental revenue*, *revenue by account*, GL/corporate view): use **`GLTransactions`** and **## Revenue** / hierarchy rules (`-SUM(t.GLNetChangeACY)` where applicable).

**Receivables turnover** and **Customer Sales on Credit** use **`ReceivablesStateTransactions`** / **`ReceivablesTransactions`** — see **# Receivables State Transaction rules** below. **Customer Net Change** uses **`ReceivablesTransactions.CUSTTRANS_AMOUNTMST`** only (not state snapshot).

### Sales customer / vendor display columns (denormalized)

Both **`SalesInvoiceTransactions`** and **`SalesInvoiceMiscChargesTransactions`** expose customer identifiers directly. **Do not** join the `Customer` dimension just to read a name.

#### Sell-to customer columns (default for sales / net sales)

| Column | Use |
|---|---|
| `SellToCustomerID` | **Default customer key** for sales / net sales (`JOIN` / `GROUP BY`) |
| `SellToCustomerName` | Display name (`MAX(...)` when grouping by `SellToCustomerID`) |
| `SellToCustomerCountry` | Sell-to country |

Default key for:

- Top customers by net sales
- New customers
- Sales / net sales by customer
- Sales customer ranking

Reason: `SellToCustomerID` is the customer who actually bought / received the sale.

#### Bill-to customer columns (only when AR / collection is involved on the sales fact)

| Column | Use |
|---|---|
| `BillToCustomerID`, `BillToCustomerName` | Pivot to AR collection responsibility |
| `BillToCustomerCountry`, `BillToCustomerGroup` | Bill-to display dimensions |

For pure receivables / AR analysis, use the equivalent columns on **`ReceivablesStateTransactions`** / **`ReceivablesTransactions`** instead — see **[Receivables customer key rule](#receivables-customer-key-rule)**.

#### Sales + Receivables comparison rule

When a question combines **sales / net sales** with **receivables**, pick the customer key by the main business intent:

| Question type | Preferred key |
|---|---|
| Pure receivables / AR ranking | `BillToCustomerID` |
| Pure sales / net sales ranking | `SellToCustomerID` |
| Top customers by net sales + their receivables balance | `SellToCustomerID` |
| Collection / AR-exposure analysis | `BillToCustomerID` |

#### Vendor display on sales fact

`SalesInvoiceTransactions` also carries a legacy `VendorName`; use it only for ad-hoc display when the user names a vendor on the invoice side. For full vendor analysis, use **`PayablesStateTransactions` / `PayablesTransactions`** + **[Payables vendor key rule](#payables-vendor-key-rule)**.

#### Customer-name anti-pattern

**Do not** drive grain on **`CustomerName`** / **`SellToCustomerName`** alone, and **do not** `UNION ALL` invoice lines with misc charges on the name column. Names can repeat / change / disagree across facts. Always aggregate by **`SellToCustomerID`** in both sales tables, combine with **`FULL OUTER JOIN`** (line totals vs discount totals), and carry a display name with **`MAX(SellToCustomerName)`**. Join **`ReceivablesStateTransactions`** on **`SellToCustomerID`** (sales view) or **`BillToCustomerID`** (AR view), not on name.

### Net sales (total) — invoice model

**Wrong:** `SUM` from `GLTransactions` on `Revenue Main Group` for “net sales”.

**Right:** Net line amount from **`SalesInvoiceTransactions`**, minus discount end from **`SalesInvoiceMiscChargesTransactions`**, EWIG, `DateID` in bounds. Output in millions with `CAST(ROUND(... / 1000000.0, 4) AS DECIMAL(18,4))` when showing millions.

```sql
DECLARE @AsOfDate DATE = '2024-12-31';

WITH Bounds AS (
    SELECT
        CAST(20240101 AS INT) AS StartDateID,
        CAST(CONVERT(CHAR(8), @AsOfDate, 112) AS INT) AS EndDateID
),

NetSalesLine AS (
    SELECT
        SUM(COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0)) AS NetSalesLineAmount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND s.DateID BETWEEN b.StartDateID AND b.EndDateID
),

DiscountEnd AS (
    SELECT
        SUM(COALESCE(m.SalesDiscountAmountEnd, 0)) AS SalesDiscountAmountEnd
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND m.DateID BETWEEN b.StartDateID AND b.EndDateID
),

Final AS (
    SELECT
        COALESCE(n.NetSalesLineAmount, 0)
        - COALESCE(d.SalesDiscountAmountEnd, 0) AS NetSales
    FROM NetSalesLine n
    CROSS JOIN DiscountEnd d
)

SELECT
    CAST(
        ROUND(NetSales / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS NetSales_Mn
FROM Final;
```

Use `<StartDateID>` / `<EndDateID>` or `DECLARE @AsOfDate` as needed; confirm column names against the warehouse.

### Net sales by customer + receivables (top-N pattern)

**Wrong:** one subquery `UNION ALL` lines and misc on **`CustomerName`**, then `GROUP BY CustomerName`; joining receivables on **`CustomerName`**.

**Right:** same two-branch net sales model as company total, but **group by `SellToCustomerID`** in **`NetSalesLine`** and **`DiscountEnd`**, then **`FULL OUTER JOIN`** so customers with only lines or only misc discounts still get a row. Receivables snapshot: **`MAX(DateID)`** in bounds, then **`SUM(ReceivablesBalance)`** grouped by **`SellToCustomerID`**, **`LEFT JOIN`** to top customers on **`SellToCustomerID`**.

```sql
WITH Bounds AS (
    SELECT
        CAST(20250101 AS INT) AS StartDateID,
        CAST(20251231 AS INT) AS EndDateID
),

NetSalesLine AS (
    SELECT
        s.SellToCustomerID,
        MAX(s.CustomerName) AS CustomerName,
        SUM(COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0)) AS NetSalesLineAmount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND s.DateID BETWEEN b.StartDateID AND b.EndDateID
      AND s.SellToCustomerID IS NOT NULL
    GROUP BY
        s.SellToCustomerID
),

DiscountEnd AS (
    SELECT
        m.SellToCustomerID,
        SUM(COALESCE(m.SalesDiscountAmountEnd, 0)) AS SalesDiscountAmountEnd
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND m.DateID BETWEEN b.StartDateID AND b.EndDateID
      AND m.SellToCustomerID IS NOT NULL
    GROUP BY
        m.SellToCustomerID
),

NetSalesByCustomer AS (
    SELECT
        COALESCE(n.SellToCustomerID, d.SellToCustomerID) AS CustomerID,
        n.CustomerName,
        COALESCE(n.NetSalesLineAmount, 0)
        - COALESCE(d.SalesDiscountAmountEnd, 0) AS NetSales
    FROM NetSalesLine n
    FULL OUTER JOIN DiscountEnd d
        ON n.SellToCustomerID = d.SellToCustomerID
),

TopCustomers AS (
    SELECT TOP 10
        CustomerID,
        CustomerName,
        NetSales
    FROM NetSalesByCustomer
    ORDER BY
        NetSales DESC
),

LatestReceivablesDate AS (
    SELECT
        MAX(r.DateID) AS LatestDateID
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN b.StartDateID AND b.EndDateID
),

ReceivablesBalanceByCustomer AS (
    SELECT
        r.SellToCustomerID AS CustomerID,
        SUM(r.ReceivablesBalance) AS ReceivablesBalance
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    INNER JOIN LatestReceivablesDate ld
        ON r.DateID = ld.LatestDateID
    WHERE cm.Code = 'EWIG'
      AND r.SellToCustomerID IS NOT NULL
    GROUP BY
        r.SellToCustomerID
)

SELECT
    tc.CustomerName,
    CAST(ROUND(tc.NetSales / 1000000.0, 4) AS DECIMAL(18,4)) AS NetSales_2025_Mn,
    CAST(ROUND(COALESCE(rb.ReceivablesBalance, 0) / 1000000.0, 4) AS DECIMAL(18,4)) AS ReceivablesBalance_2025_Mn
FROM TopCustomers tc
LEFT JOIN ReceivablesBalanceByCustomer rb
    ON tc.CustomerID = rb.CustomerID
ORDER BY
    tc.NetSales DESC;
```

### Item-level net sales (`ItemName`)

Both facts expose **`ItemName`** directly:

- **`SalesInvoiceTransactions.ItemName`**
- **`SalesInvoiceMiscChargesTransactions.ItemName`**

For **item-level net sales**, use **`ItemName`** on each table. **Do not** join **`Item`** unless the user needs extra item attributes (dimensions not on the fact).

**Net sales** = net sales line − sales discount amount end (same as total, scoped by item):

| Component | Source |
|-----------|--------|
| Net sales line | `SUM(SalesInvoiceTransactions.CUSTINVOICETRANS_LINEAMOUNTMST)` |
| Sales discount amount end | `SUM(SalesInvoiceMiscChargesTransactions.SalesDiscountAmountEnd)` |

Apply the **same** `ItemName`, **`DateID`** bounds, and **`Community`** (`cm.Code = 'EWIG'`) in **both** branches.

**Important**

- **Do not** join `SalesInvoiceTransactions` to `SalesInvoiceMiscChargesTransactions` at row level. Aggregate each table in its own CTE (same pattern as total net sales), then combine in `Final`.
- Use **`ItemName`** filters only when the question is **item-level** (named item, SKU line, product line on invoices).

**Known `ItemName` values (both sales facts)** — use **`=`** with the **exact** string (case/spacing as stored). When the user describes an item informally, pick the matching row below; there are **duplicate labels** with different codes (e.g. two *Municipality registration fees*, two *Damage Charges*—disambiguate by code prefix).

```text
00033257 - Transfer Contract Fee
00058840 - Accommodation/Leasing
00058581 - COOLING CHARGE
SERV163 - Scrap Sales
SERV0107 - Water Expenses
00033254 - Short Extension Fee
00000002 - Rent - Managed
SERV0043 - Legal Fees
00077523 - Overstay Fee
00000003 - Security Deposit
4191111008 - Bounced Cheque Fee
00033256 - New Contract Fee
00000006 - Parking Charges
4191111009 - Asset Mngt & Advisory Services
00033134 - Contract Renewal Fee
00038544 - Municipality registration fees
00077525 - Renewal Penalty Fee
00077524 - Additional Overstay fee
N/A
00000011 - Postponed Cheque Fee
00037884 - Authority Charges
00038217 - Rent - Managed Commercial
00048023 - Control Account
00038388 - Municipality registration fees
SERV0027 - Electricity Expenses
SRV00414 - Utility Charge
00000015 - Admin Fee
00059469 - Contract Fee
00000010 - Replaced Cheque Fee
00000018 - Service Fee
00038195 - Contract extension short
00038389 - VAT Payable
ITEM-000000046 - Termination Fee
00059464 - Laundry Service
PROD-000283 - Retention Receivable
ITEM-000000043 - Damage Charges
00059463 - Facility Management Service
00059465 - Access Card Registration
00000001 - Rent - Owned
00000007 - Transfer Fee
00000005 - Cancellation Charges
SERV0105 - Water & Electrcity (Direct)
None - None
Customer Advance - Customer Advance
00059460 - Catering Services
00000016 - Damage Charges
```

Example (*Net sales for item "00000001 - Rent - Owned" in 2025*):

```sql
DECLARE @AsOfDate DATE = '2025-12-31';

WITH Bounds AS (
    SELECT
        CAST(20250101 AS INT) AS StartDateID,
        CAST(CONVERT(CHAR(8), @AsOfDate, 112) AS INT) AS EndDateID
),

NetSalesLine AS (
    SELECT
        SUM(COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0)) AS NetSalesLineAmount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND s.ItemName = '00000001 - Rent - Owned'
      AND s.DateID BETWEEN b.StartDateID AND b.EndDateID
),

DiscountEnd AS (
    SELECT
        SUM(COALESCE(m.SalesDiscountAmountEnd, 0)) AS SalesDiscountAmountEnd
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND m.ItemName = '00000001 - Rent - Owned'
      AND m.DateID BETWEEN b.StartDateID AND b.EndDateID
),

Final AS (
    SELECT
        COALESCE(n.NetSalesLineAmount, 0)
        - COALESCE(d.SalesDiscountAmountEnd, 0) AS NetSales
    FROM NetSalesLine n
    CROSS JOIN DiscountEnd d
)

SELECT
    CAST(
        ROUND(NetSales / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS NetSales_2025_Mn
FROM Final;
```

### Net Sales grouping by denormalized columns

Base formula is unchanged: `SUM(CUSTINVOICETRANS_LINEAMOUNTMST) − SUM(SalesDiscountAmountEnd)`. For **grouped** Net Sales, apply the **same** grouping column(s) in **both** components (line table and misc-charges table).

| User asks by | Use column |
|---|---|
| Customer | `SellToCustomerID`, `SellToCustomerName` |
| Item | `ItemName` |
| Building | `BuildingName` (or `FDBuildingID`) |
| Community | `CommunityName` (or `FDCommunityID` + `Community`) |
| Location | `LocationName` |

Preferred customer-level pattern (compact `UNION ALL` + `GROUP BY`):

```sql
WITH NetSalesComponents AS (
    SELECT
        s.SellToCustomerID,
        s.SellToCustomerName,
        COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0) AS Amount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND s.DateID BETWEEN <StartDateID> AND <EndDateID>

    UNION ALL

    SELECT
        m.SellToCustomerID,
        m.SellToCustomerName,
        -COALESCE(m.SalesDiscountAmountEnd, 0) AS Amount
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND m.DateID BETWEEN <StartDateID> AND <EndDateID>
)
SELECT
    SellToCustomerID,
    MAX(SellToCustomerName) AS SellToCustomerName,
    SUM(Amount) AS NetSales
FROM NetSalesComponents
GROUP BY
    SellToCustomerID;
```

**Do not** row-level `JOIN` `SalesInvoiceTransactions` with `SalesInvoiceMiscChargesTransactions` — that duplicates amounts. Aggregate each side, then combine (`UNION ALL` + `GROUP BY` here, or `FULL OUTER JOIN` when AR is involved — see **[Net sales by customer + receivables (top-N pattern)](#net-sales-by-customer--receivables-top-n-pattern)**).

### New customers (sell-to, net-sales definition)

**Wrong:** `COUNT(DISTINCT SellToCustomerID)` (or customer dimension key) from invoice transactions where `DateID` falls only inside the target year. That counts **everyone who bought in the year**, including **existing** customers.

**Right:** **New customers** for calendar period **`[CurrStartDateID, CurrEndDateID]`** are **`SellToCustomerID`** values with **net sales > 0 in that window** and **no net sales on any `DateID` strictly before `CurrStartDateID`**.

Net sales for this logic matches the dependency-style model:

- **Invoice lines:** `SalesInvoiceTransactions` — use line amount in accounting currency (example column: `CUSTINVOICETRANS_LINEAMOUNTMST`; confirm exact name in warehouse).
- **Discounts:** `SalesInvoiceMiscChargesTransactions` — subtract **`SalesDiscountAmountEnd`** (emit as negative amount in the union).

Always filter **`Community`** with **`cm.Code = 'EWIG'`** on **`FDCommunityID`** for both fact tables.

Bounds must include **all history up to `CurrEndDateID`** when building per-customer prior vs current splits (not only rows inside the target year).

Reference pattern:

```sql
DECLARE @AsOfDate DATE = '2025-12-31';

WITH Bounds AS (
    SELECT
        CAST(20250101 AS INT) AS CurrStartDateID,
        CAST(CONVERT(CHAR(8), @AsOfDate, 112) AS INT) AS CurrEndDateID
),

NetSalesComponents AS (
    SELECT
        s.SellToCustomerID,
        s.DateID,
        COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0) AS Amount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND s.DateID <= b.CurrEndDateID
      AND s.SellToCustomerID IS NOT NULL

    UNION ALL

    SELECT
        m.SellToCustomerID,
        m.DateID,
        -COALESCE(m.SalesDiscountAmountEnd, 0) AS Amount
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND m.DateID <= b.CurrEndDateID
      AND m.SellToCustomerID IS NOT NULL
),

CustomerNetSales AS (
    SELECT
        n.SellToCustomerID,

        SUM(CASE
                WHEN n.DateID BETWEEN b.CurrStartDateID AND b.CurrEndDateID
                THEN n.Amount
                ELSE 0
            END) AS CurrentPeriodNetSales,

        SUM(CASE
                WHEN n.DateID < b.CurrStartDateID
                THEN n.Amount
                ELSE 0
            END) AS PriorNetSales
    FROM NetSalesComponents n
    CROSS JOIN Bounds b
    GROUP BY
        n.SellToCustomerID
)

SELECT
    COUNT(DISTINCT SellToCustomerID) AS NewCustomers
FROM CustomerNetSales
WHERE CurrentPeriodNetSales > 0
  AND COALESCE(PriorNetSales, 0) = 0;
```

If physical table names differ (e.g. `[Sales Invoice Transactions]` vs `SalesInvoiceTransactions`), use the names from the warehouse catalog — **do not** invent columns.

\---

# Receivables State Transaction rules

Use **`ReceivablesStateTransactions`** for receivables balance, overdue receivables, before-due receivables, receivables overdue %, average receivables, and receivables turnover days.

Use **`ReceivablesTransactions`** for **Customer Net Change** and **Customer Sales on Credit** (flow / transaction measures)—see **[Customer Net Change rule](#customer-net-change-rule)** and turnover section below.

`ReceivablesStateTransactions` is a state/snapshot table.  
Do not blindly sum balance values across the full date range.

\---

## Main table: `ReceivablesStateTransactions`

Important columns:

| Column | Meaning |
|---|---|
| `DateID` | Date key in `YYYYMMDD` format |
| `FDCommunityID` | Join to `Community.FinancialDimension4ID` |
| `SellToCustomerID` | Customer key — align with sales facts for net sales + AR combined reports |
| `CustomerName` | Display name when present; prefer `SellToCustomerID` for joins |
| `ReceivablesBalance` | Closing receivables balance amount |
| `hReceivablesBalanceSum` | Daily receivables balance amount used for average/turnover-style measures |
| `ReceivablesStateTransactions_DueDays` | Due-days value used to classify before-due and overdue receivables |

Default join:

```sql
FROM ReceivablesStateTransactions r
INNER JOIN Community cm
    ON r.FDCommunityID = cm.FinancialDimension4ID
```

Default community:

```sql
cm.Code = 'EWIG'
```

## Customer Net Change rule

Use **`ReceivablesTransactions`** for **Customer Net Change**.

Customer Net Change is a **transaction / flow** measure (activity in a `DateID` range), **not** a snapshot balance. **Do not** use **`ReceivablesStateTransactions`** for Customer Net Change.

### Important columns (`ReceivablesTransactions`)

| Column | Meaning |
|---|---|
| `DateID` | Date key in `YYYYMMDD` format |
| `FDCommunityID` | Join to `Community.FinancialDimension4ID` |
| `CUSTTRANS_AMOUNTMST` | Confirmed physical column for Customer Net Change |

### Confirmed formula

```text
Customer Net Change = SUM(rt.CUSTTRANS_AMOUNTMST)
```

Filter with **`cm.Code = 'EWIG'`** and **`rt.DateID`** in the requested bounds. Apply **`CAST(ROUND(... / 1000000.0, 4) AS DECIMAL(18,4))`** when the question expects millions.

```sql
SELECT
    CAST(
        ROUND(SUM(rt.CUSTTRANS_AMOUNTMST) / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS CustomerNetChange_Mn
FROM ReceivablesTransactions rt
INNER JOIN Community cm
    ON rt.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
  AND rt.DateID BETWEEN <StartDateID> AND <EndDateID>;
```

## Receivables Balance rule

Receivables Balance is a snapshot/latest-date measure.

Use the latest `DateID` in the selected period.  
Do not sum `ReceivablesBalance` across every date in the period.

SQL pattern:

```sql
WITH LatestDate AS (
    SELECT
        MAX(r.DateID) AS LatestDateID
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN <StartDateID> AND <EndDateID>
)
SELECT
    SUM(r.ReceivablesBalance) AS ReceivablesBalance
FROM ReceivablesStateTransactions r
INNER JOIN Community cm
    ON r.FDCommunityID = cm.FinancialDimension4ID
INNER JOIN LatestDate ld
    ON r.DateID = ld.LatestDateID
WHERE cm.Code = 'EWIG';
```

For millions:

```sql
CAST(ROUND(ReceivablesBalance / 1000000.0, 4) AS DECIMAL(18,4))
```

## Receivables DueDays rule

For receivables before-due and overdue logic, use:

```text
r.ReceivablesStateTransactions_DueDays
```

Do not join **Receivables Due Analysis** for basic before-due/overdue logic if `ReceivablesStateTransactions_DueDays` is available.

Rules:

```text
DueDays <= 0  = Before due
DueDays > 0   = Overdue / After due
```

## Receivables Before Due

```sql
SUM(CASE
        WHEN r.ReceivablesStateTransactions_DueDays <= 0
        THEN r.ReceivablesBalance
        ELSE 0
    END) AS ReceivablesBeforeDue
```

## Receivables Overdue

```sql
SUM(CASE
        WHEN r.ReceivablesStateTransactions_DueDays > 0
        THEN r.ReceivablesBalance
        ELSE 0
    END) AS ReceivablesOverdue
```

## Receivables Balance + Overdue + Overdue % pattern

Use this pattern when the user asks:

- receivables balance  
- overdue receivables  
- receivables overdue %  
- before-due receivables  
- receivables due status  

```sql
WITH LatestDate AS (
    SELECT
        MAX(r.DateID) AS LatestDateID
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN <StartDateID> AND <EndDateID>
),
agg AS (
    SELECT
        SUM(r.ReceivablesBalance) AS ReceivablesBalance,

        SUM(CASE
                WHEN r.ReceivablesStateTransactions_DueDays <= 0
                THEN r.ReceivablesBalance
                ELSE 0
            END) AS ReceivablesBeforeDue,

        SUM(CASE
                WHEN r.ReceivablesStateTransactions_DueDays > 0
                THEN r.ReceivablesBalance
                ELSE 0
            END) AS ReceivablesOverdue
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    INNER JOIN LatestDate ld
        ON r.DateID = ld.LatestDateID
    WHERE cm.Code = 'EWIG'
)
SELECT
    CAST(ROUND(ReceivablesBalance / 1000000.0, 4) AS DECIMAL(18,4)) AS ReceivablesBalance_Mn,
    CAST(ROUND(ReceivablesBeforeDue / 1000000.0, 4) AS DECIMAL(18,4)) AS ReceivablesBeforeDue_Mn,
    CAST(ROUND(ReceivablesOverdue / 1000000.0, 4) AS DECIMAL(18,4)) AS ReceivablesOverdue_Mn,
    CAST(
        ROUND(
            CASE
                WHEN ReceivablesBalance IS NULL OR ReceivablesBalance = 0 THEN NULL
                ELSE (ReceivablesOverdue * 100.0) / ReceivablesBalance
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS ReceivablesOverduePercent
FROM agg;
```

## Receivables bucket rule using DueDays

For receivables aging bucket questions, use **`ReceivablesStateTransactions_DueDays`**.

Do not use `Group1`, `Group2`, or `Group3` for now.

Bucket mapping:

```text
DueDays <= -91        → Before due over 90 days
DueDays -90 to -61    → Before due 61 - 90 days
DueDays -60 to -31    → Before due 31 - 60 days
DueDays -30 to 0      → Before due under 30 days

DueDays 1 to 30       → Overdue under 30 days
DueDays 31 to 60      → Overdue 31 - 60 days
DueDays 61 to 90      → Overdue 61 - 90 days
DueDays 91 to 120     → Overdue 91 - 120 days
DueDays 121 to 150    → Overdue 121 - 150 days
DueDays 151 to 180    → Overdue 151 - 180 days
DueDays 181 to 365    → Overdue 181 - 365 days
DueDays 366 to 730    → Overdue 1 - 2 years
DueDays >= 731        → Overdue over 2 years
```

Boundary rule:

- `DueDays = 90` → Overdue 61 - 90 days  
- `DueDays = 91` → Overdue 91 - 120 days  
- `DueDays = -90` → Before due 61 - 90 days  
- `DueDays = -91` → Before due over 90 days  

SQL pattern:

```sql
WITH LatestDate AS (
    SELECT
        MAX(r.DateID) AS LatestDateID
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN <StartDateID> AND <EndDateID>
),
bucketed AS (
    SELECT
        CASE
            WHEN r.ReceivablesStateTransactions_DueDays <= -91 THEN 'Before due over 90 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN -90 AND -61 THEN 'Before due 61 - 90 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN -60 AND -31 THEN 'Before due 31 - 60 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN -30 AND 0 THEN 'Before due under 30 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 1 AND 30 THEN 'Overdue under 30 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 31 AND 60 THEN 'Overdue 31 - 60 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 61 AND 90 THEN 'Overdue 61 - 90 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 91 AND 120 THEN 'Overdue 91 - 120 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 121 AND 150 THEN 'Overdue 121 - 150 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 151 AND 180 THEN 'Overdue 151 - 180 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 181 AND 365 THEN 'Overdue 181 - 365 days'
            WHEN r.ReceivablesStateTransactions_DueDays BETWEEN 366 AND 730 THEN 'Overdue 1 - 2 years'
            WHEN r.ReceivablesStateTransactions_DueDays >= 731 THEN 'Overdue over 2 years'
        END AS DueBucket,

        CASE
            WHEN r.ReceivablesStateTransactions_DueDays <= 0 THEN 'Before due'
            WHEN r.ReceivablesStateTransactions_DueDays > 0 THEN 'Overdue'
        END AS DueStatus,

        r.ReceivablesBalance AS ReceivablesAmount
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    INNER JOIN LatestDate ld
        ON r.DateID = ld.LatestDateID
    WHERE cm.Code = 'EWIG'
)
SELECT
    DueStatus,
    DueBucket,
    CAST(ROUND(SUM(ReceivablesAmount) / 1000000.0, 4) AS DECIMAL(18,4)) AS ReceivablesAmount_Mn
FROM bucketed
WHERE DueBucket IS NOT NULL
GROUP BY
    DueStatus,
    DueBucket;
```

## Average Receivables rule

Average Receivables is **not** latest-date balance.

It is the average of daily receivables balances across the selected period.

Use **`hReceivablesBalanceSum`**.

SQL pattern:

```sql
WITH DailyReceivables AS (
    SELECT
        r.DateID,
        SUM(r.hReceivablesBalanceSum) AS DailyReceivablesBalance
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN <StartDateID> AND <EndDateID>
    GROUP BY
        r.DateID
)
SELECT
    AVG(CAST(DailyReceivablesBalance AS DECIMAL(38,10))) AS AverageReceivables
FROM DailyReceivables;
```

## Receivables Turnover Days rule

**Disambiguation:** If the user says **turnover days** / **DIO**-style wording **without** naming **payables**, **AP**, **vendor**, or **vendor purchase on credit**, use **this Receivables Turnover Days** pattern. Use **Payables Turnover Days** ( **`PayablesStateTransactions`** + **`PayablesTransactions`** / vendor purchase on credit) only when the question clearly refers to payables/AP/vendor.

Measure logic:

```text
Receivables Turnover Days =
Average Receivables / Customer Sales on Credit * NumberOfDays
```

The measure lookup confirms **Receivables Turnover Days** depends on **Average Receivables** and **Customer Sales on Credit**.

Use:

- **Average Receivables** = average daily receivables balance from **`ReceivablesStateTransactions`** (`hReceivablesBalanceSum` per `DateID`, then `AVG`).  
- **Customer Sales on Credit** = **`SUM([CustomerSalesonCredit])`** from **`ReceivablesTransactions`** (EWIG). Warehouse column name spelling **`CustomerSalesonCredit`** as below — if metadata differs, map from catalog first.  
- **NumberOfDays** = calendar days in the selected window (e.g. **365** for full year **20250101–20251231**).

Canonical SQL (full year **2025** example — replace **`Bounds`** for other periods):

```sql
WITH Bounds AS (
    SELECT
        CAST(20250101 AS INT) AS StartDateID,
        CAST(20251231 AS INT) AS EndDateID,
        365 AS NumberOfDays
),

DailyReceivables AS (
    SELECT
        r.DateID,
        SUM(r.hReceivablesBalanceSum) AS DailyReceivablesBalance
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN b.StartDateID AND b.EndDateID
    GROUP BY
        r.DateID
),

AverageReceivables AS (
    SELECT
        AVG(CAST(DailyReceivablesBalance AS DECIMAL(38,10))) AS AverageReceivables
    FROM DailyReceivables
),

CustomerSalesCredit AS (
    SELECT
        SUM([CustomerSalesonCredit]) AS CustomerSalesOnCredit
    FROM ReceivablesTransactions rt
    INNER JOIN Community cm
        ON rt.FDCommunityID = cm.FinancialDimension4ID
    CROSS JOIN Bounds b
    WHERE cm.Code = 'EWIG'
      AND rt.DateID BETWEEN b.StartDateID AND b.EndDateID
)

SELECT
    CAST(
        ROUND(
            CASE
                WHEN cs.CustomerSalesOnCredit IS NULL OR cs.CustomerSalesOnCredit = 0 THEN NULL
                ELSE (ar.AverageReceivables * b.NumberOfDays * 1.0) / cs.CustomerSalesOnCredit
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS ReceivablesTurnoverDays_2025
FROM AverageReceivables ar
CROSS JOIN CustomerSalesCredit cs
CROSS JOIN Bounds b;
```

### Monthly rolling-N pattern (rolling avg, rolling sum, etc.)

**Applies to:** any “rolling 3 / 6 / 12 month” / “trailing N months” style measure on monthly grain, regardless of fact table (GL revenue, sales, receivables, payables, etc.).

**Wrong:** build **`MonthPeriods`** for only the display year and then `AVG(...) OVER (ORDER BY YearMonth ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)`. Early months in the display year have no preceding rows to look back into, so the window silently shrinks — e.g. Jan-2025 averages only Jan-2025, Feb-2025 averages Jan–Feb, etc. Result is **not** a true 12-month average for those months.

**Right:** the **`MonthPeriods`** scaffold must start at **`(DisplayYear - 1) * 100 + 01`** (i.e. **N − 1 months before the first display month**) and the **fact** CTE must aggregate across that same extended window. Compute the rolling metric for the full extended series, then **filter to the display window in the final `SELECT`** (e.g. `WHERE YearMonth BETWEEN 202501 AND 202512`).

Reusable scaffold (replace `<DisplayYear>` / window length **N = 12**):

```sql
WITH MonthPeriods AS (
    SELECT
        CAST(
            CONVERT(CHAR(6),
                DATEADD(MONTH, v.n, DATEFROMPARTS(<DisplayYear> - 1, 1, 1)),
                112
            ) AS INT
        ) AS YearMonth
    FROM (
        VALUES
            (0),(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),
            (12),(13),(14),(15),(16),(17),(18),(19),(20),(21),(22),(23)
    ) v(n)
),

MonthlyFact AS (
    /* Aggregate the fact across the FULL extended window:
       DateID BETWEEN (<DisplayYear>-1)*10000 + 0101 AND <DisplayYear>*10000 + 1231 */
    SELECT
        t.DateID / 100 AS YearMonth,
        SUM(<metric_expression>) AS MetricValue
    FROM <fact_table> t
    INNER JOIN Community cm
        ON t.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND t.DateID BETWEEN
          (<DisplayYear> - 1) * 10000 + 101
          AND <DisplayYear> * 10000 + 1231
    GROUP BY
        t.DateID / 100
),

MonthlyData AS (
    SELECT
        mp.YearMonth,
        COALESCE(mf.MetricValue, 0) AS MetricValue
    FROM MonthPeriods mp
    LEFT JOIN MonthlyFact mf
        ON mp.YearMonth = mf.YearMonth
),

Rolling AS (
    SELECT
        YearMonth,
        MetricValue,
        AVG(CAST(MetricValue AS DECIMAL(38,10))) OVER (
            ORDER BY YearMonth
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS Metric_12M_RollingAvg
    FROM MonthlyData
)

SELECT
    YearMonth,
    CAST(ROUND(MetricValue / 1000000.0, 4) AS DECIMAL(18,4)) AS Metric_Mn,
    CAST(ROUND(Metric_12M_RollingAvg / 1000000.0, 4) AS DECIMAL(18,4)) AS Metric_12M_RollingAvg_Mn
FROM Rolling
WHERE YearMonth BETWEEN <DisplayYear> * 100 + 1 AND <DisplayYear> * 100 + 12
ORDER BY
    YearMonth;
```

**Rules:**

- For rolling-**N**, both **`MonthPeriods`** and the fact window must extend **`N − 1`** months before the first display month.
- Average **raw** monthly values inside the window function; only round / convert to millions in the final projection.
- Use `COALESCE(..., 0)` for missing months so the window function isn't fed NULLs.
- Do **not** self-join the monthly CTE to itself just to feed the window — `AVG(...) OVER (ORDER BY YearMonth ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)` on **`MonthlyData`** is sufficient.

Anti-pattern (from a bad generation):

```text
-- WRONG: MonthPeriods only has 2025 months.
-- Jan-2025 ends up averaging just Jan-2025; Feb-2025 averages Jan+Feb; ...
WITH MonthPeriods AS (
    SELECT 2025 * 100 + v.MonthNo AS YearMonth
    FROM (VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12)) v(MonthNo)
)
```

### Monthly receivables: snapshot balance, overdue %, turnover by `YearMonth`

Use **`DateID / 100`** as **`YearMonth`** (`YYYYMM` integer) for month grain.

**SQL Server rule:** You **cannot** write `AVG(SUM(...))` in a single `SELECT` (Msg 130). **Average receivables per month** = first **`SUM(hReceivablesBalanceSum)` per `DateID`**, then **`AVG` those daily totals** grouped by month — use **`DailyReceivables`** → **`MonthlyAvgReceivables`**.

Monthly **balance / overdue** use **latest `DateID` per month** on `ReceivablesBalance` (snapshot).

**Turnover days per month:** **`NumberOfDays`** must be **calendar days in that month** (`DAY(EOMONTH(DATEFROMPARTS(year, month, 1)))`). Do **not** use **`COUNT(DISTINCT DateID)`** from the fact table — that under/overstates when data is sparse or partial.

**Report grid:** Build **`MonthPeriods`** for all calendar months in the year, then **`LEFT JOIN`** metrics so months with no activity still appear (NULLs).

Use one **`BaseReceivables`** CTE (EWIG + date range) for snapshot + daily aggregates to avoid redundant scans.

Canonical pattern (full calendar year **2025** — replace year / bounds as needed):

```sql
WITH MonthPeriods AS (
    SELECT
        2025 * 100 + v.MonthNo AS YearMonth,
        DAY(EOMONTH(DATEFROMPARTS(2025, v.MonthNo, 1))) AS NumberOfDays
    FROM (
        VALUES
            (1), (2), (3), (4), (5), (6),
            (7), (8), (9), (10), (11), (12)
    ) v(MonthNo)
),

BaseReceivables AS (
    SELECT
        r.DateID,
        r.DateID / 100 AS YearMonth,
        r.ReceivablesBalance,
        r.hReceivablesBalanceSum,
        r.ReceivablesStateTransactions_DueDays
    FROM ReceivablesStateTransactions r
    INNER JOIN Community cm
        ON r.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND r.DateID BETWEEN 20250101 AND 20251231
),

MonthlyLatest AS (
    SELECT
        YearMonth,
        MAX(DateID) AS LatestDateID
    FROM BaseReceivables
    GROUP BY
        YearMonth
),

MonthlySnapshot AS (
    SELECT
        br.YearMonth,
        SUM(br.ReceivablesBalance) AS ReceivablesBalance,
        SUM(CASE
                WHEN br.ReceivablesStateTransactions_DueDays > 0
                THEN br.ReceivablesBalance
                ELSE 0
            END) AS ReceivablesOverdue
    FROM BaseReceivables br
    INNER JOIN MonthlyLatest ml
        ON br.YearMonth = ml.YearMonth
       AND br.DateID = ml.LatestDateID
    GROUP BY
        br.YearMonth
),

DailyReceivables AS (
    SELECT
        YearMonth,
        DateID,
        SUM(hReceivablesBalanceSum) AS DailyReceivablesBalance
    FROM BaseReceivables
    GROUP BY
        YearMonth,
        DateID
),

MonthlyAvgReceivables AS (
    SELECT
        YearMonth,
        AVG(CAST(DailyReceivablesBalance AS DECIMAL(38,10))) AS AverageReceivables
    FROM DailyReceivables
    GROUP BY
        YearMonth
),

MonthlySalesOnCredit AS (
    SELECT
        rt.DateID / 100 AS YearMonth,
        SUM(rt.CustomerSalesonCredit) AS CustomerSalesOnCredit
    FROM ReceivablesTransactions rt
    INNER JOIN Community cm
        ON rt.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND rt.DateID BETWEEN 20250101 AND 20251231
    GROUP BY
        rt.DateID / 100
)

SELECT
    mp.YearMonth,

    CAST(
        ROUND(ms.ReceivablesBalance / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS ReceivablesBalance_Mn,

    CAST(
        ROUND(ms.ReceivablesOverdue / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS ReceivablesOverdue_Mn,

    CAST(
        ROUND(
            CASE
                WHEN ms.ReceivablesBalance IS NULL OR ms.ReceivablesBalance = 0 THEN NULL
                ELSE (ms.ReceivablesOverdue * 100.0) / ms.ReceivablesBalance
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS ReceivablesOverduePercent,

    CAST(
        ROUND(
            CASE
                WHEN soc.CustomerSalesOnCredit IS NULL OR soc.CustomerSalesOnCredit = 0 THEN NULL
                ELSE (ar.AverageReceivables * mp.NumberOfDays * 1.0) / soc.CustomerSalesOnCredit
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS ReceivablesTurnoverDays

FROM MonthPeriods mp
LEFT JOIN MonthlySnapshot ms
    ON mp.YearMonth = ms.YearMonth
LEFT JOIN MonthlyAvgReceivables ar
    ON mp.YearMonth = ar.YearMonth
LEFT JOIN MonthlySalesOnCredit soc
    ON mp.YearMonth = soc.YearMonth
ORDER BY
    mp.YearMonth;
```

## Receivables customer key rule (denormalized)

`ReceivablesStateTransactions`, `ReceivablesTransactions`, and `ReceivablesDueAnalysis` expose customer identifiers directly. **Do not** join the `Customer` dimension just to read a name.

### Bill-to customer columns (default for AR)

| Column | Use |
|---|---|
| `BillToCustomerID` | **Default customer key** for receivables / AR (`JOIN` / `GROUP BY`) |
| `BillToCustomerName` | Display name (`MAX(...)` when grouping by `BillToCustomerID`) |
| `BillToCustomerCountry` | Bill-to customer country |
| `BillToCustomerGroup` | Bill-to customer group |

Default key for:

- Top customers by receivables balance
- Overdue receivables by customer
- AR aging by customer
- Receivables balance by customer
- Customer collection / payment responsibility

Reason: `BillToCustomerID` is the customer responsible for payment / receivable collection.

### Sell-to customer columns (only when sales-flavored)

| Column | Use |
|---|---|
| `SellToCustomerID`, `SellToCustomerName` | Use when ranking sales customers + their AR exposure together — see **[Sales + Receivables comparison rule](#sales--receivables-comparison-rule)** |

For pure sales / net sales analysis, use the equivalent columns on **`SalesInvoiceTransactions`** instead.

### Example (top 10 customers by receivables balance)

```sql
SELECT TOP 10
    r.BillToCustomerID,
    MAX(r.BillToCustomerName) AS BillToCustomerName,
    SUM(r.ReceivablesBalance) AS ReceivablesBalance
FROM ReceivablesStateTransactions r
WHERE r.DateID = <LatestDateID>
GROUP BY
    r.BillToCustomerID
ORDER BY
    SUM(r.ReceivablesBalance) DESC;
```

Display rule (legacy `CustomerName`): prefer **`BillToCustomerName`** over `CustomerName` when both are present; use names for display only — never as the sole join key to sales facts.

## Mistakes to avoid (Receivables State Transactions)

- Do not sum `ReceivablesBalance` across the full date range for receivables balance.  
- For Receivables Balance, use latest `DateID` in the selected period.  
- Do not join **Receivables Due Analysis** for basic overdue/before-due if `ReceivablesStateTransactions_DueDays` is available.  
- Do not use `Group1`, `Group2`, or `Group3` for receivables bucket logic for now.  
- Use `ReceivablesStateTransactions_DueDays > 0` for overdue receivables.  
- Use `ReceivablesStateTransactions_DueDays <= 0` for before-due receivables.  
- Do not calculate Average Receivables using latest-date logic.  
- Do not calculate Receivables Turnover Days until both Average Receivables and Customer Sales on Credit are resolved.  
- Do not use **`AVG(SUM(...))`** in one `SELECT` (SQL Server Msg 130); use **`DailyReceivables`** (sum per `DateID`) **then** **`MonthlyAvgReceivables`** (`AVG` by month) — see **### Monthly receivables: snapshot balance, overdue %, turnover by `YearMonth`** above.  
- For **monthly receivables turnover days**, do not use **`COUNT(DISTINCT DateID)`** as **NumberOfDays**; use **`MonthPeriods`** with **`DAY(EOMONTH(...))`** (calendar month length).
- Do not compute **Customer Net Change** from **`ReceivablesStateTransactions`**; use **`ReceivablesTransactions`** and **`SUM(CUSTTRANS_AMOUNTMST)`** — see **[Customer Net Change rule](#customer-net-change-rule)**.

\---

# Executive Finance KPI rules

Use this section for high-level business KPI questions.

**Output rule:** these KPIs return **numeric values only** — amounts in millions wrapped with `CAST(ROUND(... / 1000000.0, 4) AS DECIMAL(18,4))`; ratios / margins as `DECIMAL(18,4)` decimals. Do **not** emit text labels such as `Improving`, `Shrinking`, `Good`, `Bad`, `Cannot determine`, etc., unless the user **explicitly** asks for interpretation.

**Default scope:**

```text
Community = EWIG unless the user names another community
```

**Date semantics:**

- **Profitability KPIs** (net profit margin, profit after direct cost) → income statement **period movement** → `t.DateID BETWEEN <StartDateID> AND <EndDateID>`.
- **Balance sheet KPIs** (current ratio, working capital) → **cumulative / as-of** → `t.DateID <= <AsOfDateID>`.

Apply the global rules: revenue uses **`-SUM(t.GLNetChangeACY)`**, non-revenue GL uses **raw `SUM(t.GLNetChangeACY)`**, default community is EWIG, default date window per `# 8. Date rules` when no period is specified.

## 1. Net Profit Margin

**User phrases:** “what is our current net profit margin?”, “what is net profit margin?”.

### Definition

```text
Net Profit Margin % = Net Profit / Revenue * 100
Revenue              = Total Revenue                              (L1 = 'Revenue Main Group')
Total Expenses       = Cost + Gen & Adm Expenses                  (L1 IN ('Cost', 'Gen & Adm Expenses'))
Net Profit           = Revenue - Total Expenses
```

### SQL mapping

| Component | Filter | Aggregate |
|-----------|--------|-----------|
| Revenue | `a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'` | `-SUM(t.GLNetChangeACY)` |
| Total Expenses | `a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')` | `SUM(t.GLNetChangeACY)` |

### Standard SQL pattern

```sql
WITH agg AS (
    SELECT
        SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'
                THEN -t.GLNetChangeACY
                ELSE 0
            END) AS Revenue,

        SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')
                THEN t.GLNetChangeACY
                ELSE 0
            END) AS TotalExpenses
    FROM GLTransactions t
    INNER JOIN GLAccount a
        ON t.GLAccountID = a.GLAccountDimPKID
    INNER JOIN Community cm
        ON t.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND t.DateID BETWEEN <StartDateID> AND <EndDateID>
)
SELECT
    CAST(ROUND((Revenue - TotalExpenses) / 1000000.0, 4) AS DECIMAL(18,4)) AS NetProfit_Mn,
    CAST(
        ROUND(
            CASE
                WHEN Revenue IS NULL OR Revenue = 0 THEN NULL
                ELSE ((Revenue - TotalExpenses) * 100.0) / Revenue
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS NetProfitMarginPercent
FROM agg;
```

## 2. Profitability After Direct Costs

**User phrases:** “how profitable are we after direct costs?”, “gross profit”, “gross profit margin”, “revenue after direct cost”.

### Definition

```text
Profit After Direct Costs           = Revenue - Direct Cost
Profit After Direct Cost Margin %   = Profit After Direct Costs / Revenue * 100
```

### SQL mapping

| Component | Filter | Aggregate |
|-----------|--------|-----------|
| Revenue | `a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'` | `-SUM(t.GLNetChangeACY)` |
| Direct Cost | `a.[mainaccounthierarchy-1_L1-Name] = 'Cost'` | `SUM(t.GLNetChangeACY)` |

### Standard SQL pattern

```sql
WITH agg AS (
    SELECT
        SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'
                THEN -t.GLNetChangeACY
                ELSE 0
            END) AS Revenue,

        SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L1-Name] = 'Cost'
                THEN t.GLNetChangeACY
                ELSE 0
            END) AS DirectCost
    FROM GLTransactions t
    INNER JOIN GLAccount a
        ON t.GLAccountID = a.GLAccountDimPKID
    INNER JOIN Community cm
        ON t.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND t.DateID BETWEEN <StartDateID> AND <EndDateID>
)
SELECT
    CAST(ROUND((Revenue - DirectCost) / 1000000.0, 4) AS DECIMAL(18,4)) AS ProfitAfterDirectCost_Mn,
    CAST(
        ROUND(
            CASE
                WHEN Revenue IS NULL OR Revenue = 0 THEN NULL
                ELSE ((Revenue - DirectCost) * 100.0) / Revenue
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS ProfitAfterDirectCostMarginPercent
FROM agg;
```

## 3. Liquidity / Current Ratio

**User phrases:** “do we have enough liquidity to cover short-term liabilities?”, “current ratio”, “can current assets cover current liabilities?”.

### Definition

```text
Current Ratio = Current Assets / Current Liabilities
```

This is a **balance sheet** KPI — use **cumulative / as-of** date logic (`t.DateID <= <AsOfDateID>`).

### SQL mapping

| Component | Filter |
|-----------|--------|
| Current Assets | `a.[mainaccounthierarchy-1_L2-Name] = 'Current Assets'` |
| Current Liabilities | `a.[mainaccounthierarchy-1_L2-Name] = 'Current Liabilities'` |

Date logic: `t.DateID <= <AsOfDateID>`. Use **`ABS(...)`** on the liabilities aggregate if liabilities are stored as negative balances (typical GL convention).

### Standard SQL pattern

```sql
WITH agg AS (
    SELECT
        SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L2-Name] = 'Current Assets'
                THEN t.GLNetChangeACY
                ELSE 0
            END) AS CurrentAssets,

        ABS(SUM(CASE
                WHEN a.[mainaccounthierarchy-1_L2-Name] = 'Current Liabilities'
                THEN t.GLNetChangeACY
                ELSE 0
            END)) AS CurrentLiabilities
    FROM GLTransactions t
    INNER JOIN GLAccount a
        ON t.GLAccountID = a.GLAccountDimPKID
    INNER JOIN Community cm
        ON t.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND t.DateID <= <AsOfDateID>
)
SELECT
    CAST(ROUND(CurrentAssets / 1000000.0, 4) AS DECIMAL(18,4)) AS CurrentAssets_Mn,
    CAST(ROUND(CurrentLiabilities / 1000000.0, 4) AS DECIMAL(18,4)) AS CurrentLiabilities_Mn,
    CAST(
        ROUND(
            CASE
                WHEN CurrentLiabilities IS NULL OR CurrentLiabilities = 0 THEN NULL
                ELSE CurrentAssets / CurrentLiabilities
            END,
            4
        ) AS DECIMAL(18,4)
    ) AS CurrentRatio
FROM agg;
```

## 4. Working Capital

**User phrases:** “is working capital improving or shrinking?”, “what is working capital?”, “working capital trend”.

### Definition

```text
Working Capital = Current Assets - Current Liabilities
```

Balance sheet KPI — use **cumulative / as-of** date logic for both anchors:

```text
Current = t.DateID <= <CurrentAsOfDateID>
Prior   = t.DateID <= <PriorAsOfDateID>
```

The “improving / shrinking” trend is **computed downstream** from `WorkingCapital_Change_Mn`; do not return it as a text column in SQL unless the user explicitly asks for interpretation.

### SQL mapping

| Component | Filter |
|-----------|--------|
| Current Assets | `a.[mainaccounthierarchy-1_L2-Name] = 'Current Assets'` |
| Current Liabilities | `a.[mainaccounthierarchy-1_L2-Name] = 'Current Liabilities'` |

### Standard SQL pattern

```sql
WITH agg AS (
    SELECT
        SUM(CASE
                WHEN t.DateID <= <CurrentAsOfDateID>
                 AND a.[mainaccounthierarchy-1_L2-Name] = 'Current Assets'
                THEN t.GLNetChangeACY
                ELSE 0
            END) AS CurrentAssets_Current,

        ABS(SUM(CASE
                WHEN t.DateID <= <CurrentAsOfDateID>
                 AND a.[mainaccounthierarchy-1_L2-Name] = 'Current Liabilities'
                THEN t.GLNetChangeACY
                ELSE 0
            END)) AS CurrentLiabilities_Current,

        SUM(CASE
                WHEN t.DateID <= <PriorAsOfDateID>
                 AND a.[mainaccounthierarchy-1_L2-Name] = 'Current Assets'
                THEN t.GLNetChangeACY
                ELSE 0
            END) AS CurrentAssets_Prior,

        ABS(SUM(CASE
                WHEN t.DateID <= <PriorAsOfDateID>
                 AND a.[mainaccounthierarchy-1_L2-Name] = 'Current Liabilities'
                THEN t.GLNetChangeACY
                ELSE 0
            END)) AS CurrentLiabilities_Prior
    FROM GLTransactions t
    INNER JOIN GLAccount a
        ON t.GLAccountID = a.GLAccountDimPKID
    INNER JOIN Community cm
        ON t.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND t.DateID <= <CurrentAsOfDateID>
),
calc AS (
    SELECT
        CurrentAssets_Current - CurrentLiabilities_Current AS WorkingCapital_Current,
        CurrentAssets_Prior  - CurrentLiabilities_Prior   AS WorkingCapital_Prior
    FROM agg
)
SELECT
    CAST(ROUND(WorkingCapital_Current / 1000000.0, 4) AS DECIMAL(18,4)) AS WorkingCapital_Current_Mn,
    CAST(ROUND(WorkingCapital_Prior   / 1000000.0, 4) AS DECIMAL(18,4)) AS WorkingCapital_Prior_Mn,
    CAST(ROUND((WorkingCapital_Current - WorkingCapital_Prior) / 1000000.0, 4) AS DECIMAL(18,4)) AS WorkingCapital_Change_Mn
FROM calc;
```

**Notes for all four KPIs:**

- Always include **`Community`** (`cm.Code = 'EWIG'`) — do **not** rely on company / ledger / project filters for these KPIs.
- Keep **`-SUM`** only on the **revenue** branch of the `CASE`; non-revenue branches use raw `SUM`.
- For prior-period anchors (Working Capital), `<PriorAsOfDateID>` is typically the same calendar offset (e.g. previous year-end, previous quarter-end) — confirm from the user’s wording.
- **Numeric-only output:** amounts in `DECIMAL(18,4)` millions, ratios / margins in `DECIMAL(18,4)`. Do **not** mix string label columns into the result set; let the downstream summarizer interpret trends.

\---

# Denormalized display columns — pointers

The cross-cutting rules below have been **moved into their owning domain sections**. Use this hub to jump to the right rule for the question type.

| Need | Section |
|---|---|
| Payables: vendor key (Pay-to vs Buy-from), state ↔ transaction join | [Payables vendor key rule (denormalized)](#payables-vendor-key-rule-denormalized) |
| Receivables: customer key (Bill-to default), example top-N pattern | [Receivables customer key rule (denormalized)](#receivables-customer-key-rule-denormalized) |
| Sales / Net Sales: customer key (Sell-to default), Sales + Receivables comparison, customer-name anti-pattern | [Sales customer / vendor display columns (denormalized)](#sales-customer--vendor-display-columns-denormalized) |
| Net Sales grouped by Customer / Item / Building / Community / Location | [Net Sales grouping by denormalized columns](#net-sales-grouping-by-denormalized-columns) |
| `BuildingName` / `CommunityName` / `LocationName` on all facts | [Denormalized location columns on facts](#denormalized-location-columns-on-facts) |
| `GLTransactions.BuildingName` / `UnitName` (rental revenue, building performance) | [Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules) |
| Rental income YTD, rental yield, top-building share, asset-class revenue | [GL Rental Income, Rental Yield, Building Contribution, and Asset Class Revenue Rules](#gl-rental-income-rental-yield-building-contribution-and-asset-class-revenue-rules) |
| Units / occupancy / lease expiry / rent potential | [Real Estate / Leasing / GL Rental Revenue Rules](#real-estate--leasing--gl-rental-revenue-rules) |
| Vacancy aging, re-let time, below-average occupancy, tenant demand by area | [Vacancy, Re-let, Occupancy, and Tenant Demand Rules](#vacancy-re-let-occupancy-and-tenant-demand-rules) |
| Tenant stay, top-revenue tenants (net sales), retention / renewal trend | [Tenant Stay, Tenant Revenue, and Tenant Retention Rules](#tenant-stay-tenant-revenue-and-tenant-retention-rules) |
| Item-level Net Sales (`ItemName` on both sales tables) | [Item-level net sales (`ItemName`)](#item-level-net-sales-itemname) |

**Key vs. name rule (global):** use **IDs** for `JOIN` / `GROUP BY`. Use **names** for display only — wrap with `MAX(...)` when grouping by ID. Never join or group **only** by name when the ID is available.

\---

# 8\. Date rules

`DateID` is an integer in `YYYYMMDD` format.

## Default `DateID` window when the user gives no period

When the question has **no** year, **no** explicit `DateID` / date range, **no** month or quarter, and **no** time-intelligence keyword (YTD, MTD, QTD, WTD, last month, etc.), filter to **current year from January 1 through today**:

```sql
/* Example: fact alias t — replace with p, etc. */
AND t.DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
                 AND CAST(CONVERT(char(8), GETDATE(), 112) AS INT)
```

If the user states a **specific `20xx` year**, anchor to that year (usually `20xx0101`–`20xx1231` for a completed year, or Jan 1–today when that year is the current year and the question reads as year-to-date).

Extract year:

```sql
CAST(LEFT(CAST(t.DateID AS VARCHAR(8)), 4) AS INT)
```

Extract month:

```sql
CAST(SUBSTRING(CAST(t.DateID AS VARCHAR(8)), 5, 2) AS INT)
```

Filter full years:

```sql
t.DateID BETWEEN 20210101 AND 20251231
```

\---

# 9\. EWIG selection rule

EWIG can mean different things. Choose based on user intent.

|User meaning|Correct filter|
|-|-|
|EWIG community / confirmed revenue report|`cm.Code = 'EWIG'`|
|EWIG company/legal entity|`c.CompanyCode = 'EWIG'`|
|EWIG ledger|`l.LEDGER\_NAME = 'EWIG'`|
|EWIG project|Use `Project` only if explicitly requested|

For the confirmed revenue graph/report, EWIG means community:

```sql
cm.Code = 'EWIG'
```

\---

# 10\. Standard SQL pattern

```sql
SELECT
    <grouping\_columns>,
    <metric\_expression> AS <metric\_name>
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
<join other dimensions only if needed>
WHERE 1 = 1
  <account hierarchy filter>
  <dimension filter>
  <date filter>
GROUP BY
    <grouping\_columns>
ORDER BY
    <grouping\_columns>;
```

\---

# 11\. Confirmed query example: Total revenue by year for EWIG community

```sql
SELECT
    CAST(LEFT(CAST(t.DateID AS VARCHAR(8)), 4) AS INT) AS RevenueYear,
    CAST(
        ROUND((-SUM(t.GLNetChangeACY)) / 1000000.0, 4)
        AS DECIMAL(18,4)
    ) AS TotalRevenue\_Mn
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
WHERE a.\[mainaccounthierarchy-1\_L1-Name] = 'Revenue Main Group'
  AND cm.Code = 'EWIG'
  AND t.DateID BETWEEN 20210101 AND 20251231
GROUP BY
    CAST(LEFT(CAST(t.DateID AS VARCHAR(8)), 4) AS INT)
ORDER BY
    RevenueYear;
```

\---

# Real Estate / Leasing / GL Rental Revenue Rules

Use this section when the user asks about units, properties, buildings, occupancy, lease expiry, rental income, rental growth, or building performance.

For **portfolio rental income YTD**, **rental yield rankings**, **top-building revenue share**, and **asset-class revenue contribution**, see **[GL Rental Income, Rental Yield, Building Contribution, and Asset Class Revenue Rules](#gl-rental-income-rental-yield-building-contribution-and-asset-class-revenue-rules)**.

For **vacancy aging**, **re-let time**, **occupancy vs portfolio average**, and **tenant demand by area**, see **[Vacancy, Re-let, Occupancy, and Tenant Demand Rules](#vacancy-re-let-occupancy-and-tenant-demand-rules)**.

For **average tenant stay**, **top-revenue tenants** (net sales), and **retention / renewal trend**, see **[Tenant Stay, Tenant Revenue, and Tenant Retention Rules](#tenant-stay-tenant-revenue-and-tenant-retention-rules)**.

## Actual table names

Use these actual table names:

| Table | Use |
|---|---|
| `Unit_Unfiltered` | Current unit/property portfolio, occupancy, unit counts, vacant units, rent potential |
| `UnitLeasingWithLocation` | Lease contracts, tenants, renewals, lease expiry, contract value, leasing demand, rental growth |
| `GLTransactions` | Actual posted accounting revenue/income by building, unit, location, region |
| `GLAccount` | Account hierarchy filtering for rental revenue / revenue |
| `Community` | Default EWIG/community filtering |

Do not use `UnitWithRM`.

## Table routing rule

### Use `Unit_Unfiltered` for current portfolio / operational questions

Use `Unit_Unfiltered` for:

- how many properties are managed
- how many units are managed
- current occupancy rate
- leased units
- vacant units
- units vacant for more than X days
- buildings below average occupancy
- unit type / room category stock
- rent potential / expected annual rent

Important columns:

| Column | Use |
|---|---|
| `UnitID` | Unit count |
| `UnitName` | Unit display |
| `PropertyID` | Property/building key |
| `PropertyName` | Building/property display |
| `Status` | Leased / vacant / blocked logic |
| `StateCode` | Active unit filtering |
| `UnitTypeName` | Apartment, Villa, Commercial, Parking, etc. |
| `RoomCategory` | Studio, 1 Bedroom, 2 Bedroom, etc. |
| `UsePermitName` | Residential / Commercial |
| `UpdatedLocationName` | Area/location |
| `RentPerAnnumExcludingTax` | Rent potential/current annual unit rent |
| `TotalAreaSqft` | Area calculation |
| `HandOverDate` | Vacancy age calculation |

Default active portfolio filter:

```sql
U.StateCode = 0
AND ISNULL(U.Status, '') <> 'Blocked'
```

Occupancy formula:

Occupancy Rate % = Leased Units / Total Units * 100

SQL logic:

```sql
COUNT(DISTINCT CASE WHEN U.Status = 'Leased' THEN U.UnitID END) * 100.0
/ NULLIF(COUNT(DISTINCT U.UnitID), 0)
```

Vacant unit logic:

```sql
U.Status <> 'Leased'
AND ISNULL(U.Status, '') <> 'Blocked'
```

Vacant days logic:

```sql
DATEDIFF(DAY, CAST(U.HandOverDate AS DATE), CAST(GETDATE() AS DATE))
```

### Use `UnitLeasingWithLocation` for lease / tenant / contract questions

Use `UnitLeasingWithLocation` for:

- leases expiring in next 30 / 60 / 90 days
- leases expiring this quarter
- lease renewal rate
- tenants up for renewal
- high-value expiring leases
- properties with concentration of expiring leases
- lease value / contract value
- rental growth by area
- unit types most in demand
- new leases / renewal leases / transfer leases

Important columns:

| Column | Use |
|---|---|
| `UnitLeasingID` | Lease/contract key |
| `ID` | Contract name/number |
| `PropertyName` | Building/property display |
| `UnitName` | Unit display |
| `ContractStart` | Lease start / demand / growth period |
| `ContractEnd` | Planned lease end |
| `ActualMoveOutDate` | Actual lease end if moved out |
| `TotalContractValueAfterDiscount` | Lease/contract value |
| `LeasingType` | New / Renewal / Transfer |
| `NextStatus` | Renewal-rate logic |
| `CorporateCustomerName` | Tenant/customer |
| `PrimaryContact` | Tenant/customer fallback |
| `ContactType` | Tenant classification |
| `UsePermitName` | Residential / Commercial |
| `UpdatedLocationName` | Area/location |
| `UnitTypeName` | Unit type |
| `RoomCategory` | Studio / 1 Bedroom / 2 Bedroom |

Effective lease end date:

```sql
CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd) AS DATE)
```

Lease value:

```sql
ul.TotalContractValueAfterDiscount
```

Tenant display:

```sql
COALESCE(ul.CorporateCustomerName, ul.PrimaryContact, 'Unknown Tenant') AS TenantName
```

## GLTransactions denormalized display columns

`GLTransactions` contains these direct display columns:

| Column | Use |
|---|---|
| `BuildingName` | Building/property display and grouping |
| `UnitName` | Unit display and grouping |
| `LocationName` | Location grouping only if asked |
| `RegionName` | Region grouping only if asked |

Default output rule: show **names** by default, not IDs.

Use `t.BuildingName` for building/property output.

Use `t.UnitName` for unit output.

Do not show `t.FDBuildingID`, `t.FDUnitID`, `t.LocationName`, or `t.RegionName` unless the user explicitly asks for IDs, location, or region.

## GL rental revenue rule

Use `GLTransactions` when the user asks for **actual** rental revenue, rental income generated, income from buildings, or revenue by building/unit from GL.

Do **not** use `Unit_Unfiltered.RentPerAnnumExcludingTax` for actual posted rental revenue. That column is only for rent potential/current annual unit rent.

Rental revenue amount:

```sql
-SUM(t.GLNetChangeACY)
```

Rental revenue account filter:

```sql
a.[mainaccounthierarchy-1_L7] = '4111111'
```

Default community filter:

```sql
cm.Code = 'EWIG'
```

Default date logic if no period is given:

```sql
t.DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
AND CAST(CONVERT(CHAR(8), GETDATE(), 112) AS INT)
```

### Rental revenue by building from GL

When the user asks: rental revenue by building, rental income by property, which buildings generated most rental income, building-wise rental income from GL:

- Use `t.BuildingName`
- `GROUP BY t.BuildingName`
- Amount: `-SUM(t.GLNetChangeACY)`
- Filter: `a.[mainaccounthierarchy-1_L7] = '4111111'`

Do not show building ID unless explicitly asked.

### Rental revenue by unit from GL

When the user asks: rental revenue by unit, unit-wise rental income, which units generated most rental revenue:

- Use `t.UnitName`
- `GROUP BY t.UnitName`
- Amount: `-SUM(t.GLNetChangeACY)`
- Filter: `a.[mainaccounthierarchy-1_L7] = '4111111'`

If unit names may repeat across buildings, include `t.BuildingName, t.UnitName` in output/`GROUP BY`, but still do not show `FDUnitID` unless explicitly asked.

### Building performance using GL rental revenue

For actual building rental performance, use GL rental revenue, not `RentPerAnnumExcludingTax`.

Logic:

- GL Rental Revenue = `-SUM(GLNetChangeACY)`
- GL Rental Revenue Per Unit = GL Rental Revenue / Total Units
- Portfolio Average GL Rental Revenue Per Unit = `AVG(Building GL Rental Revenue Per Unit)`
- Underperforming Building = Building GL Rental Revenue Per Unit < Portfolio Average
- Top Performing Building = Building GL Rental Revenue Per Unit > Portfolio Average

| Table | Column | Use |
|---|---|---|
| `GLTransactions` | `BuildingName` | Revenue grouping |
| `GLTransactions` | `GLNetChangeACY` | Revenue amount |
| `GLTransactions` | `DateID` | Revenue period |
| `GLAccount` | `mainaccounthierarchy-1_L7` | Rental revenue filter (`4111111`) |
| `Unit_Unfiltered` | `PropertyName` | Match to `GLTransactions.BuildingName` |
| `Unit_Unfiltered` | `UnitID` | Total unit count |
| `Unit_Unfiltered` | `Status` | Leased/vacant count |
| `Unit_Unfiltered` | `StateCode` | Active portfolio filter |

Join/match building names:

```sql
t.BuildingName = U.PropertyName
```

Use `Unit_Unfiltered` only for unit count/occupancy. Use `GLTransactions` for revenue.

## Rent potential vs actual GL revenue

| Source | Column / table | When to use |
|---|---|---|
| Rent potential | `Unit_Unfiltered.RentPerAnnumExcludingTax` | rent potential, current annual rent, expected annual rent, vacant unit rent, portfolio rent potential |
| Actual posted revenue | `GLTransactions.GLNetChangeACY` | actual rental income, rental revenue generated, GL rental revenue, revenue by building/unit, income by property |
| Lease / contract value | `UnitLeasingWithLocation.TotalContractValueAfterDiscount` | lease value, contract value, expiring lease value, renewal value, tenant contract amount |

## Unit type demand rule

If the user asks which **unit types** are most in demand (studio vs 1BHK vs 2BHK), group by `COALESCE(ul.RoomCategory, ul.UnitTypeName)` on `UnitLeasingWithLocation` with the same last-90-day demand logic as **[4. Areas with highest tenant demand right now](#4-areas-with-highest-tenant-demand-right-now)**.

## Rental growth by area rule

If the user asks: which areas are seeing fastest rental growth, rental growth by location, area-wise rent growth — use `UnitLeasingWithLocation`.

- Area: `ul.UpdatedLocationName`
- Date: `ul.ContractStart`
- Rent/value: `ul.TotalContractValueAfterDiscount`

Growth formula:

Rental Growth % = (Current Avg Lease Value - Prior Avg Lease Value) / Prior Avg Lease Value * 100

Default comparison: current YTD vs prior-year same YTD period.

Use **average** lease value, not total lease value, so larger areas are not favored only because they have more contracts.

## Lease expiry / renewal rule

Use `UnitLeasingWithLocation` for: leases expiring in next 30/60/90 days, leases expiring this quarter, lease renewal rate, tenants up for renewal, high-value expiring leases, concentration of expiring leases by property.

For **retention trend over 12 months** (current vs prior period), see **[3. Tenant retention improved in the last 12 months](#3-tenant-retention-improved-in-the-last-12-months)**.

Do **not** use `GLTransactions` for lease expiry or renewal pipeline questions.

Effective lease end date:

```sql
CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd) AS DATE)
```

Lease value: `ul.TotalContractValueAfterDiscount`

Renewal flag: `ul.NextStatus = 'Renewal'`

Renewal rate formula:

Renewal Rate % = Renewed expired contracts / Total expired contracts * 100

```sql
COUNT(DISTINCT CASE WHEN ul.NextStatus = 'Renewal' THEN ul.UnitLeasingID END) * 100.0
/ NULLIF(COUNT(DISTINCT ul.UnitLeasingID), 0)
```

## Mistakes to avoid (Real Estate / Leasing)

* Do not use `UnitWithRM`.
* Do not use `RentPerAnnumExcludingTax` for actual rental revenue.
* Do not use `GLTransactions` for lease expiry, renewal pipeline, or tenant renewal questions.
* Do not use `UnitLeasingWithLocation.TotalContractValueAfterDiscount` as actual posted revenue.
* Do not show building/unit IDs unless explicitly requested.
* Do not show `LocationName` or `RegionName` unless explicitly requested.
* Do not use full `Revenue Main Group` when the user specifically asks for rental revenue; use L7 code `4111111`.
* Do not use market value unless the user explicitly asks for market value.
* Do not use **`GLTransactions`** for vacancy, occupancy, re-let time, or tenant demand — see **[Vacancy, Re-let, Occupancy, and Tenant Demand Rules](#vacancy-re-let-occupancy-and-tenant-demand-rules)**.

\---

# Vacancy, Re-let, Occupancy, and Tenant Demand Rules

Use these rules for operational real-estate questions related to vacancy, occupancy, re-letting, and tenant demand.

Do **not** use `GLTransactions` for these questions unless the user explicitly asks for actual posted revenue.

## Table routing

| Question type | Use table |
|---|---|
| Vacant units | `Unit_Unfiltered` |
| Current occupancy | `Unit_Unfiltered` |
| Buildings below portfolio average occupancy | `Unit_Unfiltered` |
| Average time to re-let a unit | `UnitLeasingWithLocation` |
| Tenant demand by area | `UnitLeasingWithLocation` |

## 1. Units vacant for more than 90 days

Use when the user asks: which units have been vacant for more than 90 days, long vacant units, vacant units aging, units vacant over X days.

**Table:** `Unit_Unfiltered U`

| Column | Use |
|---|---|
| `UnitID` | Unit key |
| `UnitName` | Unit display |
| `PropertyName` | Building/property display |
| `Status` | Leased / vacant / blocked status |
| `StateCode` | Active unit filter |
| `HandOverDate` | Vacancy start date |
| `UnitTypeName` | Unit type display |
| `RoomCategory` | Studio / 1 Bedroom / 2 Bedroom |
| `UsePermitName` | Residential / Commercial |

**Logic:**

- Vacant unit = status is not Leased and not Blocked
- Vacant days = `GETDATE() - HandOverDate`
- Vacant over 90 days = `VacantDays > 90` (use user-supplied **X** when they say “over X days”)

**SQL logic:**

```sql
U.StateCode = 0
AND ISNULL(U.Status, '') <> 'Blocked'
AND U.Status <> 'Leased'
AND U.HandOverDate IS NOT NULL
AND DATEDIFF(DAY, CAST(U.HandOverDate AS DATE), CAST(GETDATE() AS DATE)) > 90
```

Use `U.PropertyName AS BuildingName` for building display.

Do not use `GLTransactions` for vacancy aging.

## 2. Average time to re-let a unit in a building

Use when the user asks: average time to re-let a unit in Building X, average re-let days, average time between leases, how long does it take to lease again.

**Table:** `UnitLeasingWithLocation ul`

| Column | Use |
|---|---|
| `UnitID` | Preferred unit key for sequencing leases |
| `UnitName` | Unit display |
| `PropertyName` | Building/property filter |
| `UnitLeasingID` | Lease/contract key |
| `ContractStart` | Start of lease |
| `ContractEnd` | Planned lease end |
| `ActualMoveOutDate` | Actual move-out date |
| `ID` | Contract name/number |

**Effective lease end date:**

```sql
CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd) AS DATE)
```

**Logic:**

For each unit, order leases by `ContractStart`. Previous lease end = `COALESCE(ActualMoveOutDate, ContractEnd)`. Next lease start = next `ContractStart` for the same `UnitID`. Re-let days = `NextContractStart - PreviousLeaseEnd`. Average re-let days = `AVG(Re-let days)`.

**SQL window logic:**

```sql
LEAD(CAST(ul.ContractStart AS DATE)) OVER (
    PARTITION BY ul.UnitID
    ORDER BY CAST(ul.ContractStart AS DATE)
) AS NextContractStartDate
```

**Re-let days:**

```sql
DATEDIFF(DAY, EffectiveLeaseEndDate, NextContractStartDate)
```

Only include valid re-let events:

```sql
NextContractStartDate IS NOT NULL
AND NextContractStartDate > EffectiveLeaseEndDate
```

For building-specific questions:

```sql
ul.PropertyName = '<Building Name>'
```

Do not use `GLTransactions` for re-let timing.

## 3. Buildings below portfolio average occupancy

Use when the user asks: which buildings are below the portfolio's average occupancy, buildings with low occupancy, under-occupied buildings, occupancy below average.

**Table:** `Unit_Unfiltered U`

| Column | Use |
|---|---|
| `PropertyName` | Building/property grouping |
| `UnitID` | Unit count |
| `Status` | Leased status |
| `StateCode` | Active unit filter |

**Active portfolio filter:**

```sql
U.StateCode = 0
AND ISNULL(U.Status, '') <> 'Blocked'
```

**Building occupancy formula:**

```text
Building Occupancy % = Leased Units in Building / Total Units in Building * 100
```

```sql
COUNT(DISTINCT CASE WHEN U.Status = 'Leased' THEN U.UnitID END) * 100.0
/ NULLIF(COUNT(DISTINCT U.UnitID), 0)
```

**Portfolio occupancy formula:**

```text
Portfolio Occupancy % = Total Leased Units / Total Units * 100
```

**Below-average rule:**

```text
Building Occupancy % < Portfolio Occupancy %
```

**Default output columns:**

- `BuildingName` (use `U.PropertyName AS BuildingName`)
- `TotalUnits`
- `LeasedUnits`
- `BuildingOccupancyPercent`
- `PortfolioOccupancyPercent`
- `OccupancyGapPercent`

Do not show property IDs unless explicitly requested.

## 4. Areas with highest tenant demand right now

Use when the user asks: which areas are seeing the highest demand from tenants right now, areas with highest demand, tenant demand by location, most demanded areas.

**Table:** `UnitLeasingWithLocation ul`

| Column | Use |
|---|---|
| `UpdatedLocationName` | Area/location grouping |
| `UnitLeasingID` | Lease count |
| `ContractStart` | Recent demand period |
| `TotalContractValueAfterDiscount` | Lease value |
| `CorporateCustomerName` | Tenant name |
| `PrimaryContact` | Tenant fallback |
| `UnitTypeName` | Optional unit type breakdown |
| `RoomCategory` | Optional room category breakdown |

**Default demand period:** If the user says “right now” and gives no exact period, use **last 90 days**:

```sql
CAST(ul.ContractStart AS DATE)
BETWEEN DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
AND CAST(GETDATE() AS DATE)
```

**Demand proxy:** count of new leases started in the selected recent period:

```sql
COUNT(DISTINCT ul.UnitLeasingID)
```

**Tenant count:**

```sql
COUNT(DISTINCT COALESCE(ul.CorporateCustomerName, ul.PrimaryContact, 'Unknown Tenant'))
```

**Value metrics:**

```sql
SUM(ul.TotalContractValueAfterDiscount)
AVG(ul.TotalContractValueAfterDiscount)
```

**Grouping:** default `GROUP BY ul.UpdatedLocationName`

**Sort:**

```sql
ORDER BY NewLeaseCount DESC, TotalLeaseValue DESC
```

Do not use `GLTransactions` for tenant demand. Tenant demand is based on leasing activity, not accounting revenue.

## Common mistakes to avoid (vacancy / occupancy / demand)

* Do not use `GLTransactions` for vacancy, occupancy, re-let time, or tenant demand.
* Do not use `RentPerAnnumExcludingTax` for tenant demand.
* Do not use `UnitLeasingWithLocation` for current occupancy unless the user specifically asks for contract-based occupancy.
* For vacancy and occupancy, use `Unit_Unfiltered`.
* For re-let time and demand, use `UnitLeasingWithLocation`.
* Use `PropertyName` as building display.
* Use `UpdatedLocationName` as area/location display.
* Use names by default, not IDs.
* Do not show IDs unless the user explicitly asks for IDs.

\---

# Tenant Stay, Tenant Revenue, and Tenant Retention Rules

Use these rules for tenant-level leasing, revenue, and retention questions.

## 1. Average length of stay for tenants

Use when the user asks: average length of stay for tenants, average tenant stay, how long do tenants stay, average lease duration.

**Table:** `UnitLeasingWithLocation ul`

| Column | Use |
|---|---|
| `UnitLeasingID` | Lease/contract key |
| `ContractStart` | Lease start date |
| `ContractEnd` | Planned lease end date |
| `ActualMoveOutDate` | Actual move-out date if available |
| `CorporateCustomerName` | Tenant name |
| `PrimaryContact` | Tenant fallback name |
| `ContactType` | Tenant classification |

**Tenant name:**

```sql
COALESCE(ul.CorporateCustomerName, ul.PrimaryContact, 'Unknown Tenant') AS TenantName
```

**Effective lease end date:**

```sql
CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd, GETDATE()) AS DATE)
```

**Length of stay formula:**

```text
Length of Stay Days = Effective Lease End Date - Contract Start Date
```

```sql
DATEDIFF(
    DAY,
    CAST(ul.ContractStart AS DATE),
    CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd, GETDATE()) AS DATE)
)
```

**Average length of stay:**

```sql
AVG(StayDays)
```

Also provide years if useful: `AVG(StayDays) / 365.0`

**Rules:**

- Use `UnitLeasingWithLocation`, not `GLTransactions`.
- Do not use receivables or sales tables for tenant stay.
- Exclude rows where `ContractStart` is null.
- Exclude invalid rows where effective end date is before contract start.

## 2. Top-revenue tenants this year

Use when the user asks: top-revenue tenants this year, top tenants by revenue, top customers by revenue, highest revenue tenants.

**Tables (sales / net sales model):**

- `SalesInvoiceTransactions s`
- `SalesInvoiceMiscChargesTransactions m`
- `Community cm`

| Table | Column | Use |
|---|---|---|
| `SalesInvoiceTransactions` | `SellToCustomerID` | Default tenant/customer key for sales revenue |
| `SalesInvoiceTransactions` | `SellToCustomerName` | Tenant/customer display |
| `SalesInvoiceTransactions` | `CUSTINVOICETRANS_LINEAMOUNTMST` | Sales invoice line amount |
| `SalesInvoiceMiscChargesTransactions` | `SellToCustomerID` | Same customer key for discount component |
| `SalesInvoiceMiscChargesTransactions` | `SellToCustomerName` | Customer display |
| `SalesInvoiceMiscChargesTransactions` | `SalesDiscountAmountEnd` | Discount to subtract |
| `Community` | `Code` | Default EWIG filter |

**Net sales / tenant revenue formula:**

```text
Tenant Revenue = Net Sales
Net Sales = CUSTINVOICETRANS_LINEAMOUNTMST - SalesDiscountAmountEnd
```

**Preferred SQL pattern:** use `UNION ALL`, not a direct join between sales and misc charges (avoids row multiplication).

```sql
WITH NetSalesComponents AS (
    SELECT
        s.SellToCustomerID,
        s.SellToCustomerName,
        COALESCE(s.CUSTINVOICETRANS_LINEAMOUNTMST, 0) AS Amount
    FROM SalesInvoiceTransactions s
    INNER JOIN Community cm
        ON s.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND s.DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
          AND CAST(CONVERT(CHAR(8), GETDATE(), 112) AS INT)

    UNION ALL

    SELECT
        m.SellToCustomerID,
        m.SellToCustomerName,
        -COALESCE(m.SalesDiscountAmountEnd, 0) AS Amount
    FROM SalesInvoiceMiscChargesTransactions m
    INNER JOIN Community cm
        ON m.FDCommunityID = cm.FinancialDimension4ID
    WHERE cm.Code = 'EWIG'
      AND m.DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
          AND CAST(CONVERT(CHAR(8), GETDATE(), 112) AS INT)
)
SELECT
    SellToCustomerID,
    MAX(SellToCustomerName) AS TenantName,
    CAST(ROUND(SUM(Amount) / 1000000.0, 4) AS DECIMAL(18,4)) AS NetSales_YTD_Mn
FROM NetSalesComponents
GROUP BY SellToCustomerID
ORDER BY NetSales_YTD_Mn DESC;
```

**Date logic (“this year”):** current YTD:

```sql
DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
AND CAST(CONVERT(CHAR(8), GETDATE(), 112) AS INT)
```

**Default output:** `TenantName` / `SellToCustomerName`, `NetSales_YTD_Mn`. Group by `SellToCustomerID`; show name by default.

**Rules:**

- Use `SellToCustomerID` and `SellToCustomerName`.
- Do not use `BillToCustomerID` unless the question is receivables/collection focused.
- Do not use `CustomerName` if `SellToCustomerName` exists.
- Do not directly join `SalesInvoiceTransactions` and `SalesInvoiceMiscChargesTransactions` (can duplicate amounts).
- Use names in final output by default; show IDs only if asked.

For alternate per-customer patterns (e.g. net sales + receivables), see **### Net sales by customer + receivables** under **## Sales / Net Sales**.

## 3. Tenant retention improved in the last 12 months

Use when the user asks: has tenant retention improved in the last 12 months, tenant retention rate, lease renewal rate, retention trend, renewal performance.

**Table:** `UnitLeasingWithLocation ul`

| Column | Use |
|---|---|
| `UnitLeasingID` | Lease/contract key |
| `ContractEnd` | Planned lease end |
| `ActualMoveOutDate` | Actual end if moved out |
| `NextStatus` | Renewal indicator |
| `ContractStart` | Optional lease start context |
| `CorporateCustomerName`, `PrimaryContact` | Tenant name if tenant-level breakdown is requested |

**Effective lease end date:**

```sql
CAST(COALESCE(ul.ActualMoveOutDate, ul.ContractEnd) AS DATE) AS LeaseEndDate
```

**Renewal flag:**

```sql
ul.NextStatus = 'Renewal'
```

**Retention / renewal rate formula:**

```text
Tenant Retention Rate % = Renewed Expired Contracts / Total Expired Contracts * 100
```

```sql
COUNT(DISTINCT CASE WHEN ul.NextStatus = 'Renewal' THEN ul.UnitLeasingID END) * 100.0
/ NULLIF(COUNT(DISTINCT ul.UnitLeasingID), 0)
```

**Comparison periods** (“last 12 months improved”):

| Period | Window |
|---|---|
| Current | last 12 months from today |
| Prior | previous 12 months before that |

```sql
-- Current
LeaseEndDate BETWEEN DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))
                 AND CAST(GETDATE() AS DATE)

-- Prior
LeaseEndDate BETWEEN DATEADD(MONTH, -24, CAST(GETDATE() AS DATE))
                 AND DATEADD(DAY, -1, DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))
```

**Output values** (numeric unless interpretation is requested):

- `CurrentExpiredContracts`
- `CurrentRenewedContracts`
- `CurrentRetentionRatePercent`
- `PriorExpiredContracts`
- `PriorRenewedContracts`
- `PriorRetentionRatePercent`
- `RetentionRateChange_PercentagePoints`

**Rules:**

- Use `UnitLeasingWithLocation`, not `GLTransactions`.
- Retention is based on lease renewal behavior, not revenue.
- Use expired/effective-ended leases as denominator.
- Use `NextStatus = 'Renewal'` as renewed contract logic.
- Do not use sales or receivables tables for retention unless the user explicitly asks for revenue retention or payment retention.

## Common mistakes to avoid (tenant stay / revenue / retention)

* Do not use `GLTransactions` for tenant stay or lease retention.
* Do not use receivables/sales for average length of stay.
* Do not use `BillToCustomerID` for top-revenue tenant ranking; use `SellToCustomerID`.
* Do not join sales lines directly to misc charges rows.
* Do not use lease contract value as tenant revenue; use net sales for top-revenue tenants.
* Do not confuse **tenant demand** (new leases by area) with **retention** (renewal of expired leases).

\---

# GL Rental Income, Rental Yield, Building Contribution, and Asset Class Revenue Rules

Use these rules for portfolio rental income, rental yield, top-performing building contribution, and asset-class revenue questions.

**Default scope:**

| Setting | Default |
|---|---|
| Community | `EWIG` unless user says otherwise |
| Period | Current year YTD unless user gives another period |
| Output | Names by default, not IDs |

**Default current YTD date logic:**

```sql
t.DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
AND CAST(CONVERT(CHAR(8), GETDATE(), 112) AS INT)
```

**Default community filter:**

```sql
cm.Code = 'EWIG'
```

Standard joins for all rules in this section:

```sql
FROM GLTransactions t
INNER JOIN GLAccount a
    ON t.GLAccountID = a.GLAccountDimPKID
INNER JOIN Community cm
    ON t.FDCommunityID = cm.FinancialDimension4ID
WHERE cm.Code = 'EWIG'
```

## 1. Total rental income (portfolio YTD)

Use when the user asks: total rental income generated by the portfolio this year, total rental income this year, rental income YTD, rental revenue generated.

**Tables:** `GLTransactions t`, `GLAccount a`, `Community cm`.

Do **not** use `Unit_Unfiltered.RentPerAnnumExcludingTax` for actual rental income.

**Formula:**

```text
Rental Income = -SUM(GLNetChangeACY)
```

**Account filter (rental revenue L7):**

```sql
a.[mainaccounthierarchy-1_L7] = '4111111'
```

**Amount expression (millions):**

```sql
CAST(ROUND((-SUM(t.GLNetChangeACY)) / 1000000.0, 4) AS DECIMAL(18,4))
```

**Distinction:**

| Source | Meaning |
|---|---|
| `GLTransactions.GLNetChangeACY` | Actual posted accounting rental revenue |
| `Unit_Unfiltered.RentPerAnnumExcludingTax` | Rent potential / current annual unit rent only |

## 2. Highest and lowest rental yield by property

Use when the user asks: highest/lowest rental yield, rental yield by building/property.

**Default meaning:** Unless the user explicitly says market value, use **GL/accounting property value**. Do not mention or use market value unless the user explicitly asks for market value, valuation value, appraised value, or fair market value.

**Formula:**

```text
Rental Yield % = Rental Revenue / GL Property Value * 100
```

**Rental revenue (GLTransactions):**

```sql
-SUM(t.GLNetChangeACY)
```

```sql
a.[mainaccounthierarchy-1_L7] = '4111111'
```

**GL property value:** cumulative GL balance up to the as-of date:

```sql
t.DateID <= <AsOfDateID>
```

```sql
SUM(t.GLNetChangeACY)
```

**Default GL property value account filters:**

```sql
a.MainAccountCategory_Description IN (
    'Investment Property',
    'Property Plant & Equipment',
    'Land',
    'Capital Work-In-Progress',
    'Contract Work-In-Progress'
)
```

**Grouping / output:** `t.BuildingName` by default. Do not show `FDBuildingID` unless explicitly requested.

**Ranking:**

- Highest rental yield: `ORDER BY RentalYieldPercent DESC`
- Lowest rental yield: `ORDER BY RentalYieldPercent ASC`

Return **top 10** highest and **top 10** lowest unless the user asks for a different count.

## 3. Top-performing building income contribution

Use when the user asks: how much overall income comes from top-performing buildings, share of income from top buildings, top building contribution to income.

**Tables:** `GLTransactions t`, `GLAccount a`, `Community cm`.

**Overall income (default):** total revenue from the full revenue group:

```sql
a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'
```

```sql
-SUM(t.GLNetChangeACY)
```

**Top-performing buildings (default):** top **10** buildings by `RevenueAmount`, where:

```sql
RevenueAmount = -SUM(t.GLNetChangeACY)
```

grouped by `t.BuildingName`.

**Formula:**

```text
Top Buildings Revenue Share % = Top 10 Building Revenue / Total Portfolio Revenue * 100
```

**Important output columns (examples):**

- `TopBuildingsRevenue_YTD_Mn`
- `TotalPortfolioRevenue_YTD_Mn`
- `TopBuildingsRevenueSharePercent`

Do not show individual building IDs unless explicitly requested.

**Rental-only variation:** If the user says **rental income from top-performing buildings**, use:

```sql
a.[mainaccounthierarchy-1_L7] = '4111111'
```

If the user says **overall income**, use:

```sql
a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'
```

## 4. Asset class revenue contribution

Use when the user asks: which asset class contributes most to revenue, residential vs commercial revenue, revenue by asset class.

**Revenue source:** `GLTransactions`.

```sql
-SUM(t.GLNetChangeACY)
```

**Default revenue filter:**

```sql
a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'
```

**Rental-only filter** (when user asks specifically for rental revenue by asset class):

```sql
a.[mainaccounthierarchy-1_L7] = '4111111'
```

**Asset class source:** `Unit_Unfiltered.UsePermitName` (typical values: `Residential`, `Commercial`).

**Join / matching:**

```sql
t.BuildingName = U.PropertyName
AND t.UnitName = U.UnitName
```

**Grouping:**

```sql
GROUP BY U.UsePermitName
```

Alias as `AssetClass`.

**Formulas:**

```text
Asset Class Revenue = -SUM(GLNetChangeACY)
Asset Class Revenue Share % = Asset Class Revenue / Total Revenue * 100
```

**Output:** `AssetClass`, `Revenue_YTD_Mn`, `RevenueSharePercent` — sort by revenue descending.

## Common mistakes to avoid (portfolio rental KPIs)

* Do not use `Unit_Unfiltered.RentPerAnnumExcludingTax` for actual rental income.
* Do not use lease contract value as actual accounting revenue.
* Do not use market value unless the user explicitly asks for market value.
* Do not show building IDs or unit IDs unless explicitly requested.
* Do not show `LocationName` or `RegionName` unless explicitly requested.
* For **rental income**, use `a.[mainaccounthierarchy-1_L7] = '4111111'`.
* For **overall income/revenue**, use `a.[mainaccounthierarchy-1_L1-Name] = 'Revenue Main Group'`.
* For **rental yield**, use GL rental revenue divided by GL property value (cumulative balance to as-of date).
* For **asset class revenue**, use GL revenue joined to `Unit_Unfiltered.UsePermitName`.

\---

# 12\. Mistakes to avoid

* Do not use `SUM(t.GLNetChangeACY)` for **revenue**; use `-SUM(t.GLNetChangeACY)` for revenue.
* Do not use `-SUM(t.GLNetChangeACY)` for **non-revenue** GL amount questions (cost, expense, assets, liabilities, equity, generic GL movement); use `SUM(t.GLNetChangeACY)` unless another rule in this file overrides.
* Do not use `CompanyID = 4` for the confirmed EWIG revenue report. Use `cm.Code = 'EWIG'`.
* Do not use project columns like `ProjectDimPKID` or `ProjectName`; use `Project.FinancialDimension23ID`, `Project.Code`, and `Project.Name`.
* Do not use `FDMainAccountID` as the default account join. Use `GLAccountID`.
* Do not join unnecessary dimensions.
* Do not filter broad account terms at the wrong level. Use the most specific matching L1/L3/L5/L7 level from the hierarchy tree.
* Do not force category-description terms into L1-L7 hierarchy.
* Do not use `GLAccount.AccountCategory` for category matching for now.
* Do not treat `MainAccountCategory_Description` and L1-L7 hierarchy as interchangeable.
* If a report/category label matches `MainAccountCategory_Description`, prefer that filter.
* Do not use `a.GLAccount` for generic business-term matching; use it only when the user explicitly asks for GL account-level output or a specific GL account.
* Do not define **new customers** as `COUNT(DISTINCT customer)` with invoices only inside the year; use **net sales in period ∧ no prior net sales** (`SalesInvoiceTransactions` + `SalesInvoiceMiscChargesTransactions`, EWIG) — see **### New customers** under **## Sales / Net Sales**.
* Do not answer **net sales** with **`GLTransactions`** or **`Revenue Main Group`**; use **`SalesInvoiceTransactions` + `SalesInvoiceMiscChargesTransactions`** — see **### Net sales (total) — invoice model** under **## Sales / Net Sales**.
* Do not build **per-customer net sales** (or net sales + receivables) with **`UNION ALL` on `CustomerName`** or join receivables on name only; use **`SellToCustomerID`**, **`NetSalesLine` / `DiscountEnd`**, **`FULL OUTER JOIN`**, and receivables on **`SellToCustomerID`** — see **### Net sales by customer + receivables** under **## Sales / Net Sales**.
* Do not answer generic **turnover days** with **Payables** turnover unless the question names payables/AP/vendor; default **Receivables Turnover Days** — see **## Receivables Turnover Days rule**.
* Do not compute **Customer Net Change** from **`ReceivablesStateTransactions`**; use **`ReceivablesTransactions`** with **`SUM(rt.CUSTTRANS_AMOUNTMST)`** — see **## Customer Net Change rule** under **# Receivables State Transaction rules**.
* Do not build **rolling / trailing N-month** averages with **`MonthPeriods`** limited to the display year only; extend **`MonthPeriods`** and the fact window **N − 1** months earlier, then filter the display range in the final `SELECT` — see **### Monthly rolling-N pattern** under receivables.
* Do not use **`FDVendorID`** for payables vendor analysis; default is **`PayToVendorID`** (use `BuyFromVendorID` only when the user explicitly asks for buy-from / supplier source) — see **[Payables vendor key rule (denormalized)](#payables-vendor-key-rule-denormalized)**.
* Do not use **`SellToCustomerID`** for pure receivables / AR rankings and do not use **`BillToCustomerID`** for sales rankings; AR → `BillToCustomerID`, sales / net sales → `SellToCustomerID` — see **[Sales + Receivables comparison rule](#sales--receivables-comparison-rule)**.
* Do not re-join `Customer` / `Vendor` / `Item` / `Building` / `Community` dim tables when the fact/state row already exposes the **`*Name`** column (or `BBuyFromVendorCountry` etc.); use the denormalized column for display / `GROUP BY` — see **[Denormalized display columns — pointers](#denormalized-display-columns--pointers)**.
* Do not write **`pt.[Vendor Purchase on Credit]`** or **`VendorPurchaseOnCredit`** (camelCase `On`); the physical column on `PayablesTransactions` is **`VendorPurchaseonCredit`** (no spaces, lowercase `on`) — see **[Vendor Purchase on Credit physical column rule](#vendor-purchase-on-credit-physical-column-rule)**.
* Do not answer **total expenses** with one L1 only (e.g. `Cost` alone) or with `-SUM(...)`; use **`L1-Name IN ('Cost', 'Gen & Adm Expenses')`** and **raw `SUM(t.GLNetChangeACY)`** — see **## Total Expenses rule** under **# 7. Calculation rules**.
* Do not use **`UnitWithRM`**, **`RentPerAnnumExcludingTax`** for posted rental revenue, or **`GLTransactions`** for lease expiry/renewal — see **[Mistakes to avoid (Real Estate / Leasing)](#mistakes-to-avoid-real-estate--leasing)**.
* For **rental revenue** by building/unit, use **`GLTransactions`** with **`a.[mainaccounthierarchy-1_L7] = '4111111'`** and **`t.BuildingName` / `t.UnitName`** for display — see **[GL rental revenue rule](#gl-rental-revenue-rule)**.
* For **portfolio rental income YTD**, **rental yield**, **top-building revenue share**, or **asset-class revenue**, see **[GL Rental Income, Rental Yield, Building Contribution, and Asset Class Revenue Rules](#gl-rental-income-rental-yield-building-contribution-and-asset-class-revenue-rules)**.
* Do not use **`GLTransactions`** for **vacancy**, **occupancy**, **re-let time**, or **tenant demand** — see **[Vacancy, Re-let, Occupancy, and Tenant Demand Rules](#vacancy-re-let-occupancy-and-tenant-demand-rules)**.
* For **tenant stay**, **top-revenue tenants** (net sales YTD), or **retention / renewal trend**, see **[Tenant Stay, Tenant Revenue, and Tenant Retention Rules](#tenant-stay-tenant-revenue-and-tenant-retention-rules)**.

\---

# 13\. GL hierarchy tree

The hierarchy below is the account tree used for matching user terms to GL hierarchy filters.

\[GL\_HIERARCHY\_TREE\_START]

Hierarchy format: L1 -> L2 -> L3 -> L5 -> L7
One L1 can contain many L2 nodes.
One L2 can contain many L3 nodes.
One L3 can contain many L5 nodes.
One L5 can contain many L7 nodes.

GL hierarchy usage rules:

* Always traverse top-down: L1 -> L2 -> L3 -> L5 -> L7.
* Select only one best-fit hierarchy node for the user's term unless explicitly asked for multiple.
* Prefer the deepest valid node that directly matches user intent.
* Do not assume all revenue terms map to full L1 revenue.
* When a user asks for L3, include all L5 and L7 nodes under that L3.
* When a user asks for L5, include all L7 nodes under that L5.
* When a user asks for L7, use only that exact L7.



L1: 1 | Asset
  L2: 11 | Current Assets
    L3: 111 | Cash & Cash Equivalents
      L5: 11111 | Bank Balance
        L7: 1111111 | First Gulf  Bank
        L7: 1111112 | National Bank Abu Dhabi
        L7: 1111113 | Other Banks
        L7: 1111114 | Abu Dhabi Commercial Bank
        L7: 1111115 | Al Hilal Bank
        L7: 1111116 | Standard Chartered Bank
        L7: 1111117 | Emirates NBD
        L7: 1111118 | Commercial Bank of Dubai -(CBD)
        L7: 1111119 | Dubai Islamic Bank
        L7: 1111120 | Abu Dhabi Islamic Bank
        L7: 1111121 | Al Salam Bank
        L7: 1111122 | Finance House
        L7: 1111123 | Emirates Islamic Bank
        L7: 1111124 | Al Maryah Bank
        L7: 1111125 | Ruya Bank
      L5: 11112 | Cash Balances
        L7: 1111211 | Account  Petty Cash
    L3: 112 | Short Term Investment
      L5: 11211 | Quoted Local Shares
        L7: 1121111 | Quoted Local Shares
      L5: 11212 | Unquoted Local Shares
        L7: 1121211 | Unquoted Shares
      L5: 11213 | Quoted Overseas Shares
        L7: 1121311 | Quoted Overseas Shares
      L5: 11214 | Unquoted Overseas Shares
        L7: 1121411 | Unquoted Overseas Investments
    L3: 113 | AR, Prepayment, Deposits
      L5: 11311 | Accounts Receivables
        L7: 1131111 | Trade Receivables
        L7: 1131112 | Provision/write off Against Trade Receivables
        L7: 1131113 | Retention Receivable
        L7: 1131114 | Provision/write off Against Retention rec.
        L7: 1131115 | Due from Related Parties
        L7: 1131116 | Provision/write off Against Group copany Rec.
        L7: 1131117 | Accrued Income
        L7: 1131118 | Notes Receivables
        L7: 1131119 | Dividend Receivables
        L7: 1131120 | Other receivables
        L7: 1131121 | Tax Receivable
      L5: 11312 | Prepayments
        L7: 1131211 | Prepaid Rent
        L7: 1131212 | Prepaid Medical Insurance
        L7: 1131213 | Prepaid Others
        L7: 1131214 | Employees Account ( Grp)
        L7: 1131215 | Advance To Contractors /Suppliers
        L7: 1131216 | Prepaid Vehicle Insurance
        L7: 1131218 | Prepayments
      L5: 11313 | Deposits
        L7: 1131311 | Bank Guarantee Deposits
        L7: 1131312 | Deposit Against Rent
        L7: 1131313 | Deposit Against Water & Electricity
        L7: 1131314 | Ministry Of Labor Deposits
        L7: 1131315 | Maintenance Deposits
        L7: 1131316 | Deposits Others
    L3: 114 | WIP
      L5: 11411 | Contract WIP
        L7: 1141111 | Contract Work In Progress
      L5: 11412 | Capital Work in Progress
        L7: 1141211 | Capital Work in Progress.
      L5: 11413 | Development WIP
        L7: 1141311 | Development-WIP
    L3: 115 | Inventory
      L5: 11511 | Inventory (grp)
        L7: 1151111 | Inventory (grp)
  L2: 12 | Non Current Assets
    L3: 121 | Investment In Subsidiaries & Other Investments
      L5: 12111 | Investment In Subsidiaries
        L7: 1211111 | Investment In Subsidiaries
        L7: 1211112 | Other Investment
    L3: 122 | Long Term Investment
      L5: 12212 | Unquoted Local Shares - Long Term
        L7: 1221211 | Unquoted Local Shares - Long Term
      L5: 12214 | Unquoted Overseas Shares - Long Term
        L7: 1221411 | Unquoted Overseas Shares - Long Term
    L3: 123 | Invest In Jvs & Association
      L5: 12311 | Invest In Jvs
        L7: 1231111 | Invest In Jvs
        L7: 1231112 | Prov. Agnst Invest In Jvs
        L7: 1231113 | Invest In Association
        L7: 1231114 | Prov. Against Invest In Association
    L3: 124 | Other Investment Long Term
      L5: 12411 | Other Investment Long Term
        L7: 1241111 | Other Investment Long Term
        L7: 1241112 | Provision Against Investment
    L3: 125 | Investment Properties -IP
      L5: 12511 | IP Land
        L7: 1251111 | IP Land
        L7: 1251112 | Impairment for IP Land
      L5: 12512 | IP Buildings-
        L7: 1251211 | IP Buildings
        L7: 1251212 | IP Accudep. Buildings
        L7: 1251213 | Impairment for IP Buildings
        L7: 1251214 | IP Accudep,Impairment Buildings
        L7: 1251215 | IP Furniture, Machinery & Others
        L7: 1251216 | IP Accudep, Fur & Fix.
      L5: 12513 | IP WIP
        L7: 1251311 | IP- WIP
    L3: 126 | Property, Plant & Equipments
      L5: 12611 | PPE- Land
        L7: 1261111 | PPE- Land
        L7: 1261112 | Impairment for PPE Land
      L5: 12612 | Land Advances (Grp)
        L7: 1261211 | Land Advances (Grp)
      L5: 12613 | PPE Buildings
        L7: 1261311 | PPE Buildings-
        L7: 1261312 | Lease Hold Improvement PPE
        L7: 1261313 | PPE Accudep Buildings
        L7: 1261314 | PPE Accudep. Leasehold Improvement
        L7: 1261315 | Impairment for Buildings (PP)
        L7: 1261318 | PPE Buildings
        L7: 1261358 | PPE Buildings
      L5: 12614 | PPE Other Assets
        L7: 1261411 | Fleet
        L7: 1261412 | Furniture & Fixture
        L7: 1261413 | Vehicles-
        L7: 1261414 | Computers & Printers
        L7: 1261415 | Software
        L7: 1261416 | Office Equipment's
        L7: 1261417 | Air Craft
        L7: 1261418 | Equipment Medical
        L7: 1261419 | Biological Assets
        L7: 1261451 | Accudep Fleet
        L7: 1261452 | Accudep Furniture & Fixture
        L7: 1261453 | Accudep Vehicles
        L7: 1261454 | Accudep Computers & Printers
        L7: 1261455 | Accudep Software
        L7: 1261456 | Accudep Office Equipment's
        L7: 1261457 | Accudep Air Craft
        L7: 1261458 | Accudep Equipment Medical
      L5: 12615 | PP WIP
        L7: 1261511 | PP-WIP
      L5: 12616 | ROU
        L7: 1261611 | ROU-
    L3: 127 | Deferred Tax Asset
      L5: 12711 | Deferred Tax Asset
        L7: 1271111 | Deferred Tax Asset

L1: 2 | Liabilities
  L2: 21 | Current Liabilities
    L3: 211 | Od Account-Group
      L5: 21111 | Od Account-
        L7: 2111111 | Fgb OD
        L7: 2111112 | Adcb OD
    L3: 212 | Account Payable, Accruals
      L5: 21211 | Accounts Payable, Accruals
        L7: 2121111 | Total Accounts Payable
        L7: 2121112 | Notes Payable (Grp)
        L7: 2121113 | Due To Related Parties
        L7: 2121115 | Other Payable (Grp)
        L7: 2121116 | Tax Payable and Settlement
      L5: 21212 | Accruals
        L7: 2121211 | Accruals Expenses
        L7: 2121212 | Accr. Employees Bin. St
    L3: 213 | Loans & Advances
      L5: 21311 | Short Term Loans
        L7: 2131111 | Al Hilal Bank Loans - ST
      L5: 21312 | Accr. Interest St
        L7: 2131211 | Accrued-interest
    L3: 214 | Deferred Revenue (Grp)
      L5: 21411 | Deferred Revenue  (Grp)
        L7: 2141111 | Deferred Rental
        L7: 2141112 | Deferred Income
    L3: 215 | Other Provision (Grp1)
      L5: 21511 | Other Provision (Grp2)
        L7: 2151115 | Other Provision (Grp2)
  L2: 22 | Non Current Liability
    L3: 221 | Term Loans
      L5: 22111 | Long Term Loans
        L7: 2211111 | Fgb Bank Loan
        L7: 2211112 | Nbad Bank Loan
        L7: 2211113 | Adcb Bank Loan
        L7: 2211114 | Al Hilal Bank Loan   LT
        L7: 2211115 | Margin Trading Account
        L7: 2211116 | SCB loan account
        L7: 2211117 | Sukuk
        L7: 2211118 | CBD-loan account
        L7: 2211119 | ENBD-Facility loan
        L7: 2211120 | Long Term Loans
      L5: 22112 | Accrued Interest LT
        L7: 2211211 | Accrued Interest LT,Fgb
        L7: 2211212 | Accrued Interest LT,Adcb
        L7: 2211213 | Accrued Interest LT,Hilal
        L7: 2211214 | Accrued Interest LT,CBD
        L7: 2211215 | Accrued Interest LT,SCB
    L3: 222 | End of Service Benifit
      L5: 22211 | End of Service Benifit
        L7: 2221111 | End of Service Benifit
        L7: 2221112 | LABORS End of Service Benefit
      L5: 22212 | Accrued Pension
        L7: 2221211 | Accrue Pension-UAE Staff
        L7: 2221212 | Accrued Pensione-GCC Staff
        L7: 2221213 | Pension Payment
    L3: 223 | Deferred Revenue Long Period
      L5: 22311 | Deferred Revenue Long Period
        L7: 2231111 | Deferred Revenue Long Period
      L5: 22312 | Other Non-current Long term liabilities
        L7: 2231211 | Other Non-current Long term liabilities
    L3: 224 | Non Current Liability
      L5: 22411 | Non Current Liability
        L7: 2241114 | Non Current Liability

L1: 3 | Equity Main  Group
  L2: 31 | Equity  Group
    L3: 311 | Equity  Group
      L5: 31111 | Share Capital Group
        L7: 3111111 | Share Capital
      L5: 31112 | Statutory Reserves (Grp)
        L7: 3111211 | Statutory Reserves(Grp)
      L5: 31113 | Owner Current Account
        L7: 3111311 | Owner Current Account (Grp)
      L5: 31114 | Retained Earnings-
        L7: 3111411 | Retained Earnings (Grp)
      L5: 31115 | Fair Value Reserve
        L7: 3111511 | Fair Value Reserve (Grp)
      L5: 31116 | Revaluation Of Fixed Assets (Grp)
        L7: 3111611 | Revaluation Of Fixed Assets (Grp)
      L5: 31117 | Share Holder Contribution
        L7: 3111711 | Share Holder Contribution
      L5: 31118 | Prior Period Adjustment
        L7: 3111811 | Prior Period Adjustment

L1: 4 | Revenue Main Group
  L2: 41 | Revenue Sub Group
    L3: 411 | Rental Revenue (Grp)
      L5: 41111 | Rental Revenue (Grp)
        L7: 4111111 | Rental Revenue
      L5: 41112 | Property Management Revenue
        L7: 4111211 | Property Management Revenue
    L3: 412 | Service & Trading
      L5: 41211 | Facility Management Revenue
        L7: 4121111 | Maintenance Revenue
        L7: 4121112 | Security Guard Revenue
        L7: 4121113 | Cleaning Services
        L7: 4121114 | PMU
      L5: 41212 | Income from Recruitment Services
        L7: 4121211 | Income from Labour supply
        L7: 4121212 | Income from Watchman Supply
      L5: 41213 | Income from Industry Services
        L7: 4121311 | Income from Industry Services
      L5: 41214 | Income from Design & Fit outs
        L7: 4121411 | Income from Design & Fit outs
      L5: 41215 | Retail Operation Revenue
        L7: 4121511 | Retail Operation Revenue
        L7: 4121512 | Othe Operation Income
      L5: 41216 | Healthcare Revenue
        L7: 4121611 | Healthcare Revenue
      L5: 41217 | Taxi Revenue
        L7: 4121711 | Taxi Operating Revenue
      L5: 41218 | Workshop Revenue
        L7: 4121811 | Workshop Taxi Revenue
      L5: 41219 | Media & Publication Revenue
        L7: 4121911 | Media & Publication Revenue
      L5: 41220 | Hotel Operation Revenue
        L7: 4122011 | Hotel Operation Revenue
      L5: 41221 | Income From Government Contract
        L7: 4122111 | Income From Government Contract
    L3: 413 | Income From Sale Of Properties
      L5: 41311 | Income From Sale Of Properties
        L7: 4131111 | Income From Sale Of Properties
    L3: 414 | Income From Share Trading
      L5: 41411 | Income From Share Trading
        L7: 4141111 | Income From Share Trading
      L5: 41412 | Portfolio Valuation Gain/Loss
        L7: 4141211 | Portfolio Valuation Gain/ Loss
    L3: 415 | Dog Training Service
      L5: 41511 | Dog Training  Service
        L7: 4151111 | Dog  Training Service
    L3: 419 | Other Income
      L5: 41911 | Other Income
        L7: 4191111 | Other Income
      L5: 41912 | Dividend
        L7: 4191211 | Dividend
      L5: 41913 | Income  From Disposal Of Investment
        L7: 4191311 | Income  From Disposal Of Investment
        L7: 4191312 | Income  From Disposal Of Investment
      L5: 41914 | Income from JV & Associates
        L7: 4191411 | Income from JV & Associates-
      L5: 41915 | Interest Income
        L7: 4191511 | Interest Income
      L5: 41916 | Income From Amortization of Differed Revenue
        L7: 4191611 | Income From Amortization of Differed Revenue
      L5: 41917 | 
        L7: 4191711 | Exchange Income

L1: 5 | Cost
  L2: 51 | Direct Cost
    L3: 511 | Rental Cost
      L5: 51111 | Building Maintenance Cost
        L7: 5111111 | Preventive Maintenance Cost
        L7: 5111112 | General Maintenance Cost
        L7: 5111113 | Security Guard Cost
        L7: 5111114 | Building Cleaning Cost
        L7: 5111115 | Building Utility Cost
        L7: 5111116 | Other Building Cost
      L5: 51112 | Property Management Cost
        L7: 5111211 | Property Management Cost
    L3: 512 | Operation Cost (Grp)
      L5: 51211 | Manpower Cost (Direct)
        L7: 5121111 | Payroll Cost
        L7: 5121112 | Employee's Other Benefits (Direct)
        L7: 5121113 | Other Manpower Cost (Direct)
      L5: 51212 | Material Cost
        L7: 5121211 | Material Cost
      L5: 51213 | Sub Contract Cost
        L7: 5121311 | Sub Contract Cost
      L5: 51214 | Rent Expenses (Direct)
        L7: 5121411 | Rent Expenses (Direct)
      L5: 51215 | Other Direct Cost
        L7: 5121511 | Other Direct Cost
      L5: 51216 | Machinery & Tools Cost
        L7: 5121611 | Machinery & Tools Cost
      L5: 51217 | Design & Consulant Cost
        L7: 5121711 | Design & Consulant Cost
      L5: 51218 | Cost Retails
        L7: 5121811 | Cost of Goods Sold Retails
        L7: 5121812 | Commercial & Other Discount
      L5: 51219 | Healthcare Cost (Grp)
        L7: 5121911 | Medical Cost
      L5: 51220 | Taxi Operation Cost
        L7: 5122011 | Taxi Operation Cost
      L5: 51221 | Workshop Cost
        L7: 5122111 | Workshop Cost
      L5: 51222 | Hotel Operation Cost
        L7: 5122211 | Hotel Operation Cost
      L5: 51223 | Government Contract Cost
        L7: 5122311 | Government Contract Cost
      L5: 51224 | Dog Training Service Cost
        L7: 5122411 | Dog Training Service  Cost
    L3: 513 | Cos  Of Income From Sale Of Propertied
      L5: 51311 | Cos  Of Income From Sale Of Propertied
        L7: 5131111 | Cos  Of Income From Sale Of Propertied

L1: 6 | Gen & Adm Expenses
  L2: 61 | Gen & Adm Expenses (Group)
    L3: 611 | Gen & Adm Expenses (Sub-Group)
      L5: 61111 | Manpower Cost
        L7: 6111111 | Admin Staff Payroll Cost
        L7: 6111112 | Other Employees Benefits
        L7: 6111113 | Other- Manpower Cost
      L5: 61112 | Rent & Utilities
        L7: 6111211 | Rent Expenses (Grp)
        L7: 6111212 | Telephone & Internet Expenses
        L7: 6111213 | Water & Electricity
      L5: 61113 | Business Travel Expenses
        L7: 6111311 | Business  Travel Expenses (Grp)
      L5: 61114 | Vehicle Expenses
        L7: 6111411 | Vehicle Expenses (Grp)
      L5: 61115 | Professional Fees
        L7: 6111511 | Professional Fees (Grp)
      L5: 61116 | Business Promotion Expenses
        L7: 6111611 | Business Promotion Expenses
      L5: 61117 | Office Expenses
        L7: 6111711 | Office Expenses (Grp)
      L5: 61118 | Repair & Maintenance - Building - Offices
        L7: 6111811 | Repair & Maintenance - Building - Offices(Grp)
      L5: 61119 | Repair & Maintenance - Equipment
        L7: 6111911 | Repair & Maintenance - Equipment(Grp)
      L5: 61120 | Provision For Bad Debts
        L7: 6112011 | Provision For Bad Debts (Grp)
      L5: 61121 | Portfolio Impairment
        L7: 6112111 | Portfolio Impairment- (Grp)
      L5: 61122 | Preoperative Expenses
        L7: 6112211 | Preoperative Expenses
    L3: 612 | Finance Cost & Interest
      L5: 61211 | Finance Cost & Interest (Grp)
        L7: 6121111 | OD Interest
        L7: 6121112 | Term Loan Interest
        L7: 6121113 | Bank Charges Interest
        L7: 6121114 | Processing Fees
        L7: 6121115 | Mortgage Fees  Expenses (Grp)
        L7: 6121116 | Finanace Cost Sukuk
    L3: 613 | Depreciation
      L5: 61311 | Depreciation Ip (Grp)
        L7: 6131111 | Depreciation For Ip
      L5: 61312 | Depreciation For Pp
        L7: 6131211 | Depreciation For Pp (Grp)
    L3: 614 | Impairment
      L5: 61411 | Impairment.
        L7: 6141111 | Impairment..

L1: 7 | Off Balance Sheet Items
  L2: 71 | Off Balance Sheet Items
    L3: 711 | Off Balance Sheet Items
      L5: 71111 | Off Balance Sheet Items
        L7: 7111111 | Off Balance Sheet Items

[GL_HIERARCHY_TREE_END]