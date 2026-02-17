import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN], suppress_callback_exceptions=True)
server = app.server

# 1. BUSINESS LOGIC: SECTORS - Adjust our definition of typical margin and stock needs for different industries to simulate realistic scenarios.
SECTOR_RATIOS = {
    'retail': {'margin': 0.40, 'stock_need': 0.15, 'label': 'Retail (Store)'},
    'services': {'margin': 0.95, 'stock_need': 0.0, 'label': 'Services (Consulting)'},
    'industry': {'margin': 0.50, 'stock_need': 0.20, 'label': 'Industry (Manufacturing)'}
}

# 2. BUSINESS LOGIC: TAX ZONES -  Statutory corporate income tax rates (STRs) - OECD / Corporate Tax tatistics 2025 https://www.oecd.org/en/publications/corporate-tax-statistics-2025_6a915941-en.html and Taxing Wages 2025 https://www.oecd.org/en/publications/taxing-wages-2025_b3a95829-en.html
TAX_ZONES = {
    'eu':    {'label': 'Europe (France/Germany/Italy)',      'salary_tax': 0.85, 'corp_tax': 0.25}, #36/29/
    'us':    {'label': 'North America (USA/Canada)',     'salary_tax': 0.25, 'corp_tax': 0.21}, 
    'asia':  {'label': 'Asia (SG/HK/Japan)',      'salary_tax': 0.20, 'corp_tax': 0.17}, 
    'latam': {'label': 'South America (Brazil)',  'salary_tax': 0.60, 'corp_tax': 0.34}, 
    'afr':   {'label': 'Africa (Nigeria/SA)',       'salary_tax': 0.15, 'corp_tax': 0.30}, 
}

# --- LAYOUT ---
app.layout = dbc.Container([
    html.Br(),
    html.H2("Danki Financial Feasibility Simulator", className="text-center", style={"color": "#33FFA2", "fontWeight": "bold" }),
    html.P("Project your financial future: Scenarios, Cash Flow, and Statements.", className="text-center text-muted"),
    html.Hr(),

    dbc.Row([
        # --- LEFT COLUMN: INPUTS ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("1. Business Context"),
                dbc.CardBody([
                    html.Label("Region"),
                    dcc.Dropdown(
                        id='region-input',
                        options=[{'label': v['label'], 'value': k} for k, v in TAX_ZONES.items()],
                        value='eu', clearable=False
                    ),
                    html.Br(),
                    html.Label("Industry"),
                    dcc.Dropdown(
                        id='industry-input',
                        options=[{'label': v['label'], 'value': k} for k, v in SECTOR_RATIOS.items()],
                        value='retail', clearable=False
                    ),
                ])
            ], className="shadow-sm mb-3"),

            dbc.Card([
                dbc.CardHeader("2. Financial Inputs"),
                dbc.CardBody([
                    html.Label("Initial Investment (Assets) €"),
                    dbc.Input(id='investment', type='number', value=20000, step=1000),
                    dbc.FormText("Amortized linearly over 5 years.", color="muted"),
                    html.Br(),
                    
                    html.Label("Owner Monthly Net Salary (€)"),
                    dbc.Input(id='owner-salary', type='number', value=2000, step=100),
                    html.Br(),
                    
                    html.Label("Rent & Utilities (€)"),
                    dbc.Input(id='rent-cost', type='number', value=3000, step=100),
                    html.Br(),
                    
                    html.Label("Number of Employees"),
                    dbc.Input(id='nb-employees', type='number', value=1, min=0),
                    html.Br(),
                    
                    html.Label("Avg Employee Net Salary (€)"),
                    dbc.Input(id='emp-salary', type='number', value=2000, step=100),
                    html.Br(),

                    dbc.Button("Calculate Plan", id='btn-calculate', style={"backgroundColor": "#FF33FF", "borderColor": "#FF33FF", "color": "white" }, size="lg", className="w-100")
                ])
            ], className="shadow-sm")
        ], width=12, md=4),

        # --- RIGHT COLUMN: RESULTS ---
        dbc.Col([
            # KPIS
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Break-Even Turnover"),
                    html.H4(id='kpi-breakeven', className="text-success")
                ]), className="text-center mb-2"), width=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Corporate Tax Rate"),
                    html.H4(id='kpi-tax-rate', className="text-info")
                ]), className="text-center mb-2"), width=6),
            ]),

            # TABS
            dbc.Tabs([
                dbc.Tab(label="Net Profit Scenarios", tab_id="tab-1"),
                dbc.Tab(label="Cash Flow Scenarios", tab_id="tab-2"),
                dbc.Tab(label="Financial Table (Base)", tab_id="tab-3"),
            ], id="tabs", active_tab="tab-1"),
            
            html.Div(id="tab-content", className="p-4 bg-white border"),
            
            # HIDDEN DOWNLOAD COMPONENT
            dcc.Download(id="download-dataframe-csv"),

        ], width=12, md=8)
    ]),

    html.Br(),
    
    # --- DISCLAIMER ---
    dbc.Alert([
        html.H5("Disclaimer: Danki Helper Tool", className="alert-heading"),
        html.P("Danki is an automated simulation helper. It is NOT a certified accountant. We use simplified assumptions and industry averages to provide directional insights, but real-world results will vary based on countless factors, like variable costs. This tool is meant for educational and planning purposes only.", className="mb-0"),
        html.P("with Python/variables, Dash, Render", className="mb-0"),
        html.Hr(),
        html.P("Please triple-check all figures with a professional financial advisor.", className="mb-0 font-weight-bold"),

        # --- NEW LOGO SECTION (Bottom Right) ---
        html.Div([
            html.Span("Powered by ", className="text-muted small me-2"), # Optional text
            html.A(html.Img(src=app.get_asset_url("logo.png"),style={"height": "50px", "borderRadius": "5px"}), href="https://www.dankistudio.com", target="_blank" )
        ], className="text-end mt-3") 
    ], color="#737373", className="mt-4"),

    
    html.Br()

], fluid=True)


# --- LOGIC HELPER ---
def perform_calculations(region, industry, investment, owner_salary, rent, nb_emp, emp_salary):
    if investment is None: investment = 0
    
    # Ratios
    margin_ratio = SECTOR_RATIOS[industry]['margin']
    salary_tax_rate = TAX_ZONES[region]['salary_tax']
    corp_tax_rate = TAX_ZONES[region]['corp_tax']
    salary_multiplier = 1 + salary_tax_rate

    # Costs
    annual_amortization = investment / 5
    total_salary_cost_monthly = (owner_salary * salary_multiplier) + (nb_emp * emp_salary * salary_multiplier)
    rent_monthly = rent * 1.2
    total_yearly_fixed_costs = (total_salary_cost_monthly + rent_monthly) * 12 + annual_amortization
    
    # Break Even
    yearly_breakeven_turnover = total_yearly_fixed_costs / margin_ratio
    
    # --- PART A: SCENARIO DATA FOR GRAPHS ---
    scenarios = {'Stagnation': 1.0, 'Growth (+5%)': 1.05, 'Recession (-5%)': 0.95}
    years = ['Year 1', 'Year 2', 'Year 3']
    graph_data = []

    base_turnover = yearly_breakeven_turnover

    for name, rate in scenarios.items():
        curr_turnover = base_turnover
        p_list, cash_list = [], []
        cumulative_cash = -investment 

        for i in range(3):
            if i > 0: curr_turnover *= rate
            
            # Logic
            gross_margin = curr_turnover * margin_ratio
            ebit = gross_margin - total_yearly_fixed_costs
            tax = ebit * corp_tax_rate if ebit > 0 else 0
            net_profit = ebit - tax
            
            cash_flow_year = net_profit + annual_amortization
            cumulative_cash += cash_flow_year
            
            p_list.append(net_profit)
            cash_list.append(cumulative_cash)

        graph_data.append({'name': name, 'profit': p_list, 'cash': cash_list})

    # --- PART B: DETAILED DATAFRAME FOR TABLE/CSV (Base Scenario Only) ---
    # We use the 'Stagnation' logic (Base) for the detailed table to keep it readable
    table_rows = []
    curr_turnover = base_turnover
    cumulative_cash = -investment
    net_fixed_assets = investment
    
    for i in range(3):
        cogs = curr_turnover * (1 - margin_ratio)
        gross_margin = curr_turnover * margin_ratio
        personnel = total_salary_cost_monthly * 12
        ext_charges = rent_monthly * 12
        ebitda = gross_margin - personnel - ext_charges
        ebit = ebitda - annual_amortization
        tax = ebit * corp_tax_rate if ebit > 0 else 0
        net_profit = ebit - tax
        
        cumulative_cash += (net_profit + annual_amortization)
        net_fixed_assets -= annual_amortization
        if net_fixed_assets < 0: net_fixed_assets = 0
        
        table_rows.append({
            'Year': years[i],
            'Turnover': curr_turnover,
            'COGS': -cogs,
            'Gross Margin': gross_margin,
            'Personnel': -personnel,
            'Rent/Charges': -ext_charges,
            'EBITDA': ebitda,
            'Amortization': -annual_amortization,
            'EBIT': ebit,
            'Tax': -tax,
            'Net Profit': net_profit,
            'Cash Position': cumulative_cash,
            'Net Assets': net_fixed_assets
        })
        
    df_table = pd.DataFrame(table_rows)

    return yearly_breakeven_turnover, corp_tax_rate, graph_data, df_table


# --- MAIN CALLBACK ---
@app.callback(
    [Output('kpi-breakeven', 'children'),
     Output('kpi-tax-rate', 'children'),
     Output('tab-content', 'children')],
    [Input('btn-calculate', 'n_clicks'),
     Input('tabs', 'active_tab')],
    [State('region-input', 'value'),
     State('industry-input', 'value'),
     State('investment', 'value'),
     State('owner-salary', 'value'),
     State('rent-cost', 'value'),
     State('nb-employees', 'value'),
     State('emp-salary', 'value')]
)
def update_dashboard(n_clicks, active_tab, region, industry, investment, owner_salary, rent, nb_emp, emp_salary):
    
    be_turnover, tax_rate, graph_data, df = perform_calculations(
        region, industry, investment, owner_salary, rent, nb_emp, emp_salary
    )
    
    content = html.Div()
    years = ['Year 1', 'Year 2', 'Year 3']

    if active_tab == "tab-1":
        # --- TAB 1: PROFIT SCENARIOS (Bar Chart) ---
        fig = go.Figure()
        colors = {'Stagnation': '#33FFA2', 'Growth (+5%)': '#FF33FF', 'Recession (-5%)': '#737373'}
        
        for d in graph_data:
            fig.add_trace(go.Bar(x=years, y=d['profit'], name=d['name'], marker_color=colors[d['name']]))
            
        fig.update_layout(title="Net Profit Scenarios", barmode='group', height=350,
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict( showgrid=False, showline=False, zeroline=False), yaxis=dict( showgrid=False,  showline=False, zeroline=False))
        content = dcc.Graph(figure=fig)

    elif active_tab == "tab-2":
        # --- TAB 2: CASH SCENARIOS (Line Chart) ---
        fig = go.Figure()
        line_colors = {
                'Stagnation': '#33FFA2',     
                'Growth (+5%)': '#FF33FF',   
                'Recession (-5%)': '#737373' 
            }    
        for d in graph_data:
            fig.add_trace(go.Scatter(x=years, y=d['cash'], mode='lines+markers', name=d['name'],
                line=dict(color=line_colors.get(d['name'], 'grey'), width=3)))
            
        #fig.add_shape(type="line", x0=0, y0=0, x1=2, y1=0, line=dict(color="#33FFA2", dash="dash"))
        fig.update_layout(title="Cash Balance Scenarios", height=350,
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict( showgrid=False, showline=False, zeroline=False), yaxis=dict( showgrid=False,  showline=False, zeroline=False))
        content = dcc.Graph(figure=fig)

    elif active_tab == "tab-3":
        # --- TAB 3: TABLE & DOWNLOAD ---
        # Transpose for Excel view
        df_display = df.set_index('Year').T.reset_index()
        df_display.columns = ['Metric', 'Year 1', 'Year 2', 'Year 3']
        
        # Formatting
        for col in ['Year 1', 'Year 2', 'Year 3']:
            df_display[col] = df_display[col].apply(lambda x: f"€{x:,.0f}")

        table = dbc.Table.from_dataframe(df_display, striped=True, bordered=True, hover=True)
        
        download_btn = dbc.Button("Download CSV", id="btn-download", className="mt-3", style={"backgroundColor": "#FF33FF", "borderColor": "#FF33FF", "color": "white" })
        content = html.Div([
            html.H5("Financial Statements (Base Scenario)"),
            table,
            download_btn
        ])

    return f"€{be_turnover:,.0f}", f"{tax_rate*100:.1f}%", content


# --- DOWNLOAD CALLBACK ---
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    [State('region-input', 'value'),
     State('industry-input', 'value'),
     State('investment', 'value'),
     State('owner-salary', 'value'),
     State('rent-cost', 'value'),
     State('nb-employees', 'value'),
     State('emp-salary', 'value')],
    prevent_initial_call=True,
)
def download_data(n_clicks, region, industry, investment, owner_salary, rent, nb_emp, emp_salary):
    # Re-run calc to get the dataframe
    _, _, _, df = perform_calculations(region, industry, investment, owner_salary, rent, nb_emp, emp_salary)
    
    df_export = df.set_index('Year').T
    return dcc.send_data_frame(df_export.to_csv, "danki_financial_plan.csv")


if __name__ == '__main__':
    app.run(debug=True)