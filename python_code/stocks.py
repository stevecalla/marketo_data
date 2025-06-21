import pandas as pd

# Define the data
data = [
    {"Symbol": "GS", "Description": "GOLDMAN SACHS GROUP INC", "Asset Class": "Equity", "Market Value": 4908.16, "Cost Basis": 4918.00},
    {"Symbol": "MTN", "Description": "VAIL RESORTS INC", "Asset Class": "Equity", "Market Value": 4981.76, "Cost Basis": 4835.84},
    {"Symbol": "SGOL", "Description": "ABRDN PHYSICAL GOLD SHARES ETF", "Asset Class": "Commodity ETF", "Market Value": 9937.75, "Cost Basis": 9897.06},
    {"Symbol": "06051XWV0", "Description": "BANK OF AMERICA, 4.35% CD DUE 12/11/25", "Asset Class": "Fixed Income", "Market Value": 10004.57, "Cost Basis": 10000.00},
    {"Symbol": "06051XWZ1", "Description": "BANK OF AMERICA, 4.3% CD DUE 03/11/26", "Asset Class": "Fixed Income", "Market Value": 10006.60, "Cost Basis": 10000.00},
    {"Symbol": "06405VJH3", "Description": "BANK OF NEW YORK, 4.25% CD DUE 06/10/26", "Asset Class": "Fixed Income", "Market Value": 10000.00, "Cost Basis": 10000.00},
    {"Symbol": "588493SE7", "Description": "MERCHANTS BANK, 4.35% CD DUE 09/15/25", "Asset Class": "Fixed Income", "Market Value": 10000.48, "Cost Basis": 10000.00},
]

# Create DataFrame
df = pd.DataFrame(data)

# Calculate Gain/Loss
df["Gain/Loss $"] = df["Market Value"] - df["Cost Basis"]
df["Gain/Loss %"] = (df["Gain/Loss $"] / df["Cost Basis"]) * 100

# Format $ values
pd.options.display.float_format = '${:,.2f}'.format

# Format Gain/Loss % as percentage
df["Gain/Loss %"] = df["Gain/Loss %"].map("{:.2f}%".format)

# Print individual holdings
print("\n📊 Individual Holdings:\n")
print(df[["Symbol", "Description", "Asset Class", "Market Value", "Cost Basis", "Gain/Loss $", "Gain/Loss %"]])

# Print overall totals
total_cost = df["Cost Basis"].sum()
total_value = df["Market Value"].sum()
total_gain = total_value - total_cost
total_gain_pct = (total_gain / total_cost) * 100

print("\n📈 Total Portfolio Stats:")
print(f"Total Cost Basis:     ${total_cost:,.2f}")
print(f"Total Market Value:   ${total_value:,.2f}")
print(f"Total Gain/Loss:      ${total_gain:,.2f} ({total_gain_pct:.2f}%)")

# Group by Asset Class
grouped = df.groupby("Asset Class").agg({
    "Market Value": "sum",
    "Cost Basis": "sum",
    "Gain/Loss $": "sum"
})
grouped["Gain/Loss %"] = (grouped["Gain/Loss $"] / grouped["Cost Basis"]) * 100
grouped["Gain/Loss %"] = grouped["Gain/Loss %"].map("{:.2f}%".format)

print("\n📂 Summary by Asset Class:\n")
print(grouped)
