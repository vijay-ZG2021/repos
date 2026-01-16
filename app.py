"""
Bond Portfolio Analysis Tool - Dash Web UI
Interactive dashboard for bond portfolio analysis
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.optimize import brentq
import io
import base64
import json


# Bond calculation functions
class Bond:
    def __init__(self, face_value, coupon_rate, years_to_maturity, market_price, frequency=2, name="Bond"):
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.years_to_maturity = years_to_maturity
        self.market_price = market_price
        self.frequency = frequency
        self.name = name
        self.coupon_payment = (face_value * coupon_rate) / frequency
        self.periods = int(years_to_maturity * frequency)
        self.ytm = self._calculate_ytm()
    
    def _calculate_ytm(self):
        def price_diff(ytm):
            return self._price_at_ytm(ytm) - self.market_price
        try:
            return brentq(price_diff, -0.1, 1.0)
        except:
            return self.coupon_rate
    
    def _price_at_ytm(self, ytm):
        y = ytm / self.frequency
        if y == 0:
            return self.coupon_payment * self.periods + self.face_value
        pv_coupons = self.coupon_payment * (1 - (1 + y) ** -self.periods) / y
        pv_face = self.face_value / (1 + y) ** self.periods
        return pv_coupons + pv_face
    
    def calculate_price(self, ytm=None):
        return self._price_at_ytm(ytm if ytm else self.ytm)
    
    def calculate_macaulay_duration(self):
        y = self.ytm / self.frequency
        price = self.market_price
        weighted_time = sum(
            t * (self.coupon_payment if t < self.periods else self.coupon_payment + self.face_value) 
            / (1 + y) ** t
            for t in range(1, self.periods + 1)
        )
        return (weighted_time / price) / self.frequency
    
    def calculate_modified_duration(self):
        mac_dur = self.calculate_macaulay_duration()
        return mac_dur / (1 + self.ytm / self.frequency)
    
    def calculate_dv01(self):
        mod_dur = self.calculate_modified_duration()
        return mod_dur * self.market_price * 0.0001
    
    def calculate_convexity(self):
        y = self.ytm / self.frequency
        price = self.market_price
        conv_sum = sum(
            t * (t + 1) * (self.coupon_payment if t < self.periods else self.coupon_payment + self.face_value)
            / (1 + y) ** t
            for t in range(1, self.periods + 1)
        )
        return conv_sum / (price * (1 + y) ** 2 * self.frequency ** 2)


def validate_portfolio_data(df):
    """
    Validate portfolio data for correctness and completeness
    
    Returns:
        tuple: (is_valid, error_messages, warnings)
    """
    errors = []
    warnings = []
    
    # Check required columns (Fund_ID is optional)
    required_cols = ['Bond_Name', 'Face_Value', 'Coupon_Rate', 'Years_To_Maturity', 'Market_Price', 'Quantity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors, warnings
    
    # Note if Fund_ID is missing
    if 'Fund_ID' not in df.columns:
        warnings.append("Fund_ID column not found. All bonds will be treated as a single portfolio.")
    
    # Check for empty DataFrame
    if df.empty:
        errors.append("Portfolio data is empty. Please add at least one bond.")
        return False, errors, warnings
    
    # Validate each row
    for idx, row in df.iterrows():
        bond_name = row.get('Bond_Name', f'Row {idx+1}')
        
        # Check for missing values
        for col in required_cols:
            if pd.isna(row[col]) or row[col] == '':
                errors.append(f"{bond_name}: Missing value for {col}")
        
        # Validate Face Value
        if not pd.isna(row['Face_Value']):
            if row['Face_Value'] <= 0:
                errors.append(f"{bond_name}: Face Value must be positive (got {row['Face_Value']})")
            elif row['Face_Value'] > 1000000:
                warnings.append(f"{bond_name}: Face Value seems unusually high (${row['Face_Value']:,.0f})")
        
        # Validate Coupon Rate
        if not pd.isna(row['Coupon_Rate']):
            if row['Coupon_Rate'] < 0:
                errors.append(f"{bond_name}: Coupon Rate cannot be negative (got {row['Coupon_Rate']}%)")
            elif row['Coupon_Rate'] > 50:
                warnings.append(f"{bond_name}: Coupon Rate seems unusually high ({row['Coupon_Rate']}%)")
        
        # Validate Years to Maturity
        if not pd.isna(row['Years_To_Maturity']):
            if row['Years_To_Maturity'] <= 0:
                errors.append(f"{bond_name}: Years to Maturity must be positive (got {row['Years_To_Maturity']})")
            elif row['Years_To_Maturity'] > 100:
                errors.append(f"{bond_name}: Years to Maturity seems unrealistic (got {row['Years_To_Maturity']} years)")
            elif row['Years_To_Maturity'] > 50:
                warnings.append(f"{bond_name}: Years to Maturity is very long ({row['Years_To_Maturity']} years)")
        
        # Validate Market Price
        if not pd.isna(row['Market_Price']) and not pd.isna(row['Face_Value']):
            if row['Market_Price'] <= 0:
                errors.append(f"{bond_name}: Market Price must be positive (got ${row['Market_Price']})")
            else:
                # Check for extreme discount/premium
                price_ratio = row['Market_Price'] / row['Face_Value']
                if price_ratio < 0.3:
                    warnings.append(f"{bond_name}: Trading at extreme discount ({price_ratio*100:.1f}% of face value)")
                elif price_ratio > 2.0:
                    warnings.append(f"{bond_name}: Trading at extreme premium ({price_ratio*100:.1f}% of face value)")
        
        # Validate Quantity
        if not pd.isna(row['Quantity']):
            if row['Quantity'] <= 0:
                errors.append(f"{bond_name}: Quantity must be positive (got {row['Quantity']})")
            elif row['Quantity'] != int(row['Quantity']):
                warnings.append(f"{bond_name}: Quantity is not a whole number ({row['Quantity']})")
        
        # Validate Frequency (if provided)
        if 'Frequency' in row and not pd.isna(row['Frequency']):
            valid_frequencies = [1, 2, 4, 12]
            if row['Frequency'] not in valid_frequencies:
                errors.append(f"{bond_name}: Frequency must be 1 (annual), 2 (semi-annual), 4 (quarterly), or 12 (monthly)")
        
        # Check for reasonable YTM calculation
        if not errors:  # Only if no errors so far
            try:
                bond = Bond(
                    face_value=row['Face_Value'],
                    coupon_rate=row['Coupon_Rate'] / 100,
                    years_to_maturity=row['Years_To_Maturity'],
                    market_price=row['Market_Price'],
                    frequency=int(row.get('Frequency', 2)),
                    name=bond_name
                )
                if bond.ytm < -0.05:
                    warnings.append(f"{bond_name}: Calculated YTM is negative ({bond.ytm*100:.2f}%)")
                elif bond.ytm > 0.50:
                    warnings.append(f"{bond_name}: Calculated YTM is very high ({bond.ytm*100:.2f}%)")
            except Exception as e:
                errors.append(f"{bond_name}: Error calculating bond metrics - {str(e)}")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def calculate_portfolio_metrics(df):
    """Calculate portfolio metrics from DataFrame"""
    bonds = []
    for _, row in df.iterrows():
        bond = Bond(
            face_value=row['Face_Value'],
            coupon_rate=row['Coupon_Rate'] / 100,
            years_to_maturity=row['Years_To_Maturity'],
            market_price=row['Market_Price'],
            frequency=int(row.get('Frequency', 2)),
            name=row['Bond_Name']
        )
        bonds.append((bond, row['Quantity']))
    
    # Calculate metrics
    total_value = sum(bond.market_price * qty for bond, qty in bonds)
    portfolio_dv01 = sum(bond.calculate_dv01() * qty for bond, qty in bonds)
    
    if total_value > 0:
        portfolio_duration = sum(
            bond.calculate_modified_duration() * bond.market_price * qty
            for bond, qty in bonds
        ) / total_value
        
        portfolio_convexity = sum(
            bond.calculate_convexity() * bond.market_price * qty
            for bond, qty in bonds
        ) / total_value
    else:
        portfolio_duration = 0
        portfolio_convexity = 0
    
    # Create detailed DataFrame
    bond_details = []
    for bond, qty in bonds:
        bond_details.append({
            'Bond Name': bond.name,
            'Quantity': qty,
            'Face Value': f"${bond.face_value:,.0f}",
            'Coupon (%)': f"{bond.coupon_rate * 100:.2f}",
            'Maturity (Yrs)': f"{bond.years_to_maturity:.1f}",
            'Market Price': f"${bond.market_price:,.2f}",
            'YTM (%)': f"{bond.ytm * 100:.2f}",
            'Position Value': f"${bond.market_price * qty:,.2f}",
            'Duration': f"{bond.calculate_modified_duration():.2f}",
            'DV01': f"${bond.calculate_dv01():.2f}",
            'Position DV01': f"${bond.calculate_dv01() * qty:,.2f}",
            'Convexity': f"{bond.calculate_convexity():.2f}"
        })
    
    return {
        'total_value': total_value,
        'portfolio_dv01': portfolio_dv01,
        'portfolio_duration': portfolio_duration,
        'portfolio_convexity': portfolio_convexity,
        'bond_details': pd.DataFrame(bond_details),
        'bonds': bonds
    }


def generate_scenario_data(bonds, shift_range=(-200, 200, 25)):
    """Generate yield scenario data"""
    scenarios = []
    current_value = sum(bond.market_price * qty for bond, qty in bonds)
    
    for shift_bps in range(shift_range[0], shift_range[1] + 1, shift_range[2]):
        shift = shift_bps / 10000
        new_value = sum(bond.calculate_price(bond.ytm + shift) * qty for bond, qty in bonds)
        change = new_value - current_value
        
        scenarios.append({
            'Yield Shift (bps)': shift_bps,
            'Portfolio Value': new_value,
            'Value Change': change,
            'Change (%)': (change / current_value) * 100 if current_value > 0 else 0
        })
    
    return pd.DataFrame(scenarios)


def generate_executive_summary(metrics, scenario_df):
    """Generate executive summary with insights"""
    total_value = metrics['total_value']
    duration = metrics['portfolio_duration']
    dv01 = metrics['portfolio_dv01']
    convexity = metrics['portfolio_convexity']
    num_bonds = len(metrics['bonds'])
    
    # Calculate average YTM
    total_market_value = sum(bond.market_price * qty for bond, qty in metrics['bonds'])
    avg_ytm = sum(bond.ytm * (bond.market_price * qty) / total_market_value for bond, qty in metrics['bonds']) * 100
    
    # Get scenario impacts
    scenario_50bp_up = scenario_df[scenario_df['Yield Shift (bps)'] == 50].iloc[0]
    scenario_100bp_up = scenario_df[scenario_df['Yield Shift (bps)'] == 100].iloc[0]
    scenario_50bp_down = scenario_df[scenario_df['Yield Shift (bps)'] == -50].iloc[0]
    
    # Duration interpretation
    if duration < 3:
        duration_risk = "Low"
        duration_color = "success"
    elif duration < 7:
        duration_risk = "Moderate"
        duration_color = "warning"
    else:
        duration_risk = "High"
        duration_color = "danger"
    
    summary = html.Div([
        # Portfolio Overview
        dbc.Row([
            dbc.Col([
                html.H5("Portfolio Overview", className="text-primary mb-3"),
                html.P([
                    html.Strong("Portfolio Size: "), f"${total_value:,.2f} across {num_bonds} bonds",
                    html.Br(),
                    html.Strong("Average Yield: "), f"{avg_ytm:.2f}%",
                    html.Br(),
                    html.Strong("Interest Rate Sensitivity: "), 
                    dbc.Badge(f"{duration_risk} Risk", color=duration_color, className="ms-2")
                ])
            ], width=6),
            dbc.Col([
                html.H5("Key Metrics Explained", className="text-primary mb-3"),
                html.P([
                    html.Strong("Duration ({:.2f} years): ".format(duration)),
                    f"For every 1% increase in yields, portfolio value decreases by approximately {duration:.2f}%.",
                    html.Br(), html.Br(),
                    html.Strong("DV01 (${:,.2f}): ".format(dv01)),
                    "Portfolio loses approximately ${:,.2f} for every 1 basis point (0.01%) increase in yields.".format(dv01)
                ])
            ], width=6)
        ]),
        
        html.Hr(),
        
        # Risk Assessment
        dbc.Row([
            dbc.Col([
                html.H5("Risk Assessment", className="text-danger mb-3"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong("Scenario: Yields ↑ 50 bps (0.5%)"),
                        html.Br(),
                        f"Expected Loss: ${scenario_50bp_up['Value Change']:,.2f} ({scenario_50bp_up['Change (%)']:.2f}%)"
                    ], color="light"),
                    dbc.ListGroupItem([
                        html.Strong("Scenario: Yields ↑ 100 bps (1.0%)"),
                        html.Br(),
                        f"Expected Loss: ${scenario_100bp_up['Value Change']:,.2f} ({scenario_100bp_up['Change (%)']:.2f}%)"
                    ], color="light"),
                    dbc.ListGroupItem([
                        html.Strong("Maximum Expected 1-Day Loss (95% confidence):"),
                        html.Br(),
                        f"Approximately ${dv01 * 50 * 1.645:,.2f} (assuming 50 bps daily volatility)"
                    ], color="warning")
                ])
            ], width=6),
            dbc.Col([
                html.H5("Potential Upside", className="text-success mb-3"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong("Scenario: Yields ↓ 50 bps (0.5%)"),
                        html.Br(),
                        f"Expected Gain: ${abs(scenario_50bp_down['Value Change']):,.2f} ({abs(scenario_50bp_down['Change (%)']):,.2f}%)"
                    ], color="light"),
                    dbc.ListGroupItem([
                        html.Strong("Convexity Benefit:"),
                        html.Br(),
                        f"Convexity of {convexity:.2f} provides additional upside in declining rate environments and cushions downside when rates rise."
                    ], color="light")
                ])
            ], width=6)
        ]),
        
        html.Hr(),
        
        # Recommendations
        dbc.Row([
            dbc.Col([
                html.H5("Key Insights & Recommendations", className="text-info mb-3"),
                html.Ul([
                    html.Li([
                        html.Strong("Interest Rate View: "),
                        f"With a duration of {duration:.2f} years, this portfolio will benefit from falling rates and suffer from rising rates. ",
                        "Consider hedging strategies if rates are expected to rise." if duration > 5 else "The moderate duration provides balanced risk exposure."
                    ]),
                    html.Li([
                        html.Strong("Portfolio Construction: "),
                        f"The portfolio's average yield of {avg_ytm:.2f}% represents the current income generation. ",
                        "Diversification across different maturities helps manage reinvestment risk."
                    ]),
                    html.Li([
                        html.Strong("Monitoring: "),
                        f"Watch for yield curve changes. A ${dv01:,.2f} DV01 means daily P&L will fluctuate with market movements. ",
                        "Review positioning regularly, especially during Fed policy announcements."
                    ]),
                    html.Li([
                        html.Strong("Convexity Advantage: "),
                        f"Positive convexity of {convexity:.2f} means gains from falling rates will exceed losses from rising rates of equal magnitude, ",
                        "providing a valuable risk asymmetry."
                    ])
                ])
            ])
        ])
    ])
    
    return summary
    """Generate yield scenario data"""
    scenarios = []
    current_value = sum(bond.market_price * qty for bond, qty in bonds)
    
    for shift_bps in range(shift_range[0], shift_range[1] + 1, shift_range[2]):
        shift = shift_bps / 10000
        new_value = sum(bond.calculate_price(bond.ytm + shift) * qty for bond, qty in bonds)
        change = new_value - current_value
        
        scenarios.append({
            'Yield Shift (bps)': shift_bps,
            'Portfolio Value': new_value,
            'Value Change': change,
            'Change (%)': (change / current_value) * 100 if current_value > 0 else 0
        })
    
    return pd.DataFrame(scenarios)

def create_app():
# Initialize Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Sample data
    sample_data = pd.DataFrame({
        'Fund_ID': ['Fund_A', 'Fund_A', 'Fund_B', 'Fund_B', 'Fund_C', 'Fund_C', 'Fund_A', 'Fund_B'],
        'Bond_Name': ['Treasury 5Y', 'Corporate 10Y', 'Treasury 3Y', 'Municipal 7Y', 'Corporate 5Y', 'Treasury 10Y', 'Municipal 5Y', 'Corporate 3Y'],
        'Face_Value': [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000],
        'Coupon_Rate': [5.0, 6.0, 3.0, 4.5, 5.5, 4.0, 4.2, 3.5],
        'Years_To_Maturity': [5, 10, 3, 7, 5, 10, 5, 3],
        'Market_Price': [1044.52, 1035.66, 986.50, 1018.25, 1052.30, 1000.00, 1028.45, 995.20],
        'Quantity': [10, 5, 15, 8, 12, 6, 8, 10],
        'Frequency': [2, 2, 2, 2, 2, 2, 2, 2]
    })

# Layout
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("📊 Bond Portfolio Analysis Tool", className="text-center mb-4 mt-4"),
                html.Hr()
            ])
        ]),
        
        # Fund Filter Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("🏦 Select Fund:", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id='fund-dropdown',
                                    placeholder="Select a fund...",
                                    clearable=True,
                                    style={'width': '100%'}
                                )
                            ], width=4),
                            dbc.Col([
                                html.Div(id='fund-info', className="mt-4")
                            ], width=8)
                        ])
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Upload and Data Input Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📁 Data Input")),
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Excel File')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            }
                        ),
                        html.Div(id='upload-status', className='mt-2'),
                        html.Hr(),
                        dbc.Button("Use Sample Data", id='sample-data-btn', color="primary", className="w-100")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Portfolio Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💰 Total Value", className="card-title"),
                        html.H3(id='total-value', className="text-primary")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📉 Portfolio DV01", className="card-title"),
                        html.H3(id='portfolio-dv01', className="text-success")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("⏱️ Duration", className="card-title"),
                        html.H3(id='portfolio-duration', className="text-info")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📈 Convexity", className="card-title"),
                        html.H3(id='portfolio-convexity', className="text-warning")
                    ])
                ])
            ], width=3)
        ], className="mb-4"),
        
        # Executive Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📝 Executive Summary")),
                    dbc.CardBody([
                        html.Div(id='executive-summary')
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Bond Details Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📋 Bond Details")),
                    dbc.CardBody([
                        html.Div(id='bond-details-table')
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Scenario Analysis
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("🔮 Yield Shift Scenario Analysis")),
                    dbc.CardBody([
                        dcc.Graph(id='scenario-chart')
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📊 Scenario Table")),
                    dbc.CardBody([
                        html.Div(id='scenario-table', style={'maxHeight': '400px', 'overflowY': 'auto'})
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        # Data Validation Section - ALWAYS VISIBLE
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("✅ Data Validation Report"),
                        html.Small("Scroll here to see validation details", className="text-muted ms-2")
                    ]),
                    dbc.CardBody([
                        html.Div(id='validation-report', children=[
                            dbc.Alert([
                                html.H5("⏳ Loading validation report...", className="alert-heading"),
                                html.P("Please wait while we validate your data.", className="mb-0")
                            ], color="info")
                        ])
                    ])
                ], style={'minHeight': '200px'})  # Ensure minimum height
            ])
        ], className="mb-4"),
        
        # Hidden div to store data
        dcc.Store(id='portfolio-data'),
        dcc.Store(id='filtered-data'),
        dcc.Store(id='validation-results')
        
    ], fluid=True)


    # Callbacks
    @app.callback(
        Output('fund-dropdown', 'options'),
        Output('fund-dropdown', 'value'),
        Input('portfolio-data', 'data')
    )
    def update_fund_dropdown(json_data):
        if not json_data:
            return [], None
        
        df = pd.read_json(io.StringIO(json_data), orient='split')
        
        if 'Fund_ID' not in df.columns:
            return [{'label': 'All Bonds (No Fund ID)', 'value': 'ALL'}], 'ALL'
        
        funds = sorted(df['Fund_ID'].unique())
        options = [{'label': 'All Funds', 'value': 'ALL'}] + [{'label': fund, 'value': fund} for fund in funds]
        
        return options, 'ALL'


    @app.callback(
        Output('filtered-data', 'data'),
        Output('fund-info', 'children'),
        Input('portfolio-data', 'data'),
        Input('fund-dropdown', 'value')
    )
    def filter_by_fund(json_data, selected_fund):
        if not json_data:
            return None, ""
        
        df = pd.read_json(io.StringIO(json_data), orient='split')
        
        # If no Fund_ID column, return all data
        if 'Fund_ID' not in df.columns or selected_fund == 'ALL' or selected_fund is None:
            total_bonds = len(df)
            total_funds = len(df['Fund_ID'].unique()) if 'Fund_ID' in df.columns else 1
            info = html.Div([
                html.Span(f"📊 Showing all funds: ", className="fw-bold"),
                html.Span(f"{total_bonds} bonds across {total_funds} fund(s)")
            ])
            return df.to_json(date_format='iso', orient='split'), info
        
        # Filter by selected fund
        filtered_df = df[df['Fund_ID'] == selected_fund]
        
        if filtered_df.empty:
            info = dbc.Alert(f"⚠️ No bonds found for {selected_fund}", color="warning")
            return df.to_json(date_format='iso', orient='split'), info
        
        # Display fund info
        num_bonds = len(filtered_df)
        total_quantity = filtered_df['Quantity'].sum()
        info = html.Div([
            html.Span(f"🏦 Fund: ", className="fw-bold"),
            html.Span(f"{selected_fund} | "),
            html.Span(f"{num_bonds} bonds | "),
            html.Span(f"Total quantity: {total_quantity:.0f}")
        ])
        
        return filtered_df.to_json(date_format='iso', orient='split'), info
    @app.callback(
        Output('portfolio-data', 'data'),
        Output('upload-status', 'children'),
        Output('validation-results', 'data'),
        Input('upload-data', 'contents'),
        Input('sample-data-btn', 'n_clicks'),
        State('upload-data', 'filename')
    )
    def load_data(contents, n_clicks, filename):
        ctx = dash.callback_context
        
        # Initial load - validate sample data
        if not ctx.triggered:
            is_valid, errors, warnings = validate_portfolio_data(sample_data)
            validation = {
                'is_valid': is_valid, 
                'errors': errors, 
                'warnings': warnings, 
                'filename': 'Sample Data',
                'timestamp': pd.Timestamp.now().isoformat()
            }
            return sample_data.to_json(date_format='iso', orient='split'), "", validation
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'sample-data-btn':
            is_valid, errors, warnings = validate_portfolio_data(sample_data)
            validation = {
                'is_valid': is_valid, 
                'errors': errors, 
                'warnings': warnings, 
                'filename': 'Sample Data',
                'timestamp': pd.Timestamp.now().isoformat()
            }
            return (
                sample_data.to_json(date_format='iso', orient='split'), 
                dbc.Alert("✓ Sample data loaded successfully. See validation report below.", color="success"),
                validation
            )
        
        if trigger_id == 'upload-data' and contents:
            try:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_excel(io.BytesIO(decoded))
                
                # Validate data
                is_valid, errors, warnings = validate_portfolio_data(df)
                validation = {
                    'is_valid': is_valid, 
                    'errors': errors, 
                    'warnings': warnings, 
                    'filename': filename,
                    'timestamp': pd.Timestamp.now().isoformat()
                }
                
                if not is_valid:
                    error_msg = html.Div([
                        html.H5("❌ Data Validation Failed", className="alert-heading"),
                        html.P("Cannot load data. Please scroll down to see the detailed validation report.", className="mb-0")
                    ])
                    # Return sample data so app doesn't break, but with validation errors
                    return (
                        sample_data.to_json(date_format='iso', orient='split'), 
                        dbc.Alert(error_msg, color="danger"),
                        validation
                    )
                
                # Show success or warnings
                if warnings:
                    warning_msg = html.Div([
                        html.H5(f"✓ {filename} loaded successfully", className="alert-heading"),
                        html.P("⚠️ Some warnings were found. Scroll down to see the detailed validation report.", className="mb-0")
                    ])
                    return df.to_json(date_format='iso', orient='split'), dbc.Alert(warning_msg, color="warning"), validation
                
                success_msg = f"✓ {filename} loaded successfully with no issues. See validation report below."
                return df.to_json(date_format='iso', orient='split'), dbc.Alert(success_msg, color="success"), validation
                
            except Exception as e:
                error_msg = html.Div([
                    html.H5("❌ Error Loading File", className="alert-heading"),
                    html.P(f"Error: {str(e)}", className="mb-0")
                ])
                validation = {
                    'is_valid': False, 
                    'errors': [str(e)], 
                    'warnings': [], 
                    'filename': filename if filename else 'Unknown',
                    'timestamp': pd.Timestamp.now().isoformat()
                }
                return (
                    sample_data.to_json(date_format='iso', orient='split'), 
                    dbc.Alert(error_msg, color="danger"),
                    validation
                )
        
        # Fallback
        validation = {
            'is_valid': True, 
            'errors': [], 
            'warnings': [], 
            'filename': 'Sample Data',
            'timestamp': pd.Timestamp.now().isoformat()
        }
        return sample_data.to_json(date_format='iso', orient='split'), "", validation


    @app.callback(
        Output('total-value', 'children'),
        Output('portfolio-dv01', 'children'),
        Output('portfolio-duration', 'children'),
        Output('portfolio-convexity', 'children'),
        Output('executive-summary', 'children'),
        Output('bond-details-table', 'children'),
        Output('scenario-chart', 'figure'),
        Output('scenario-table', 'children'),
        Input('filtered-data', 'data')
    )
    def update_dashboard(json_data):
        if not json_data:
            return "", "", "", "", "", "", {}, ""
        
        df = pd.read_json(io.StringIO(json_data), orient='split')
        
        if df.empty:
            empty_msg = dbc.Alert("No bonds to display. Please select a different fund or upload data.", color="info")
            return "", "", "", "", empty_msg, "", {}, ""
        
        metrics = calculate_portfolio_metrics(df)
        
        # Summary cards
        total_value = f"${metrics['total_value']:,.2f}"
        portfolio_dv01 = f"${metrics['portfolio_dv01']:,.2f}"
        portfolio_duration = f"{metrics['portfolio_duration']:.2f} yrs"
        portfolio_convexity = f"{metrics['portfolio_convexity']:.2f}"
        
        # Scenario analysis
        scenario_df = generate_scenario_data(metrics['bonds'])
        
        # Executive summary
        executive_summary = generate_executive_summary(metrics, scenario_df)
        
        # Bond details table
        bond_table = dash_table.DataTable(
            data=metrics['bond_details'].to_dict('records'),
            columns=[{'name': i, 'id': i} for i in metrics['bond_details'].columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
            ]
        )
        
        # Scenario chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=scenario_df['Yield Shift (bps)'],
            y=scenario_df['Portfolio Value'],
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='blue', width=3),
            marker=dict(size=8)
        ))
        
        # Add horizontal line for current value
        current_value = metrics['total_value']
        fig.add_hline(y=current_value, line_dash="dash", line_color="red", 
                    annotation_text="Current Value", annotation_position="right")
        
        fig.update_layout(
            title='Portfolio Value vs Yield Shift',
            xaxis_title='Yield Shift (bps)',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        # Scenario table
        scenario_table = dash_table.DataTable(
            data=scenario_df.to_dict('records'),
            columns=[
                {'name': 'Shift (bps)', 'id': 'Yield Shift (bps)'},
                {'name': 'Value', 'id': 'Portfolio Value', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
                {'name': 'Change', 'id': 'Value Change', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
                {'name': 'Change %', 'id': 'Change (%)', 'type': 'numeric', 'format': {'specifier': '.2f'}}
            ],
            style_cell={'textAlign': 'right', 'padding': '8px', 'fontSize': '12px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'filter_query': '{Change (%)} < 0', 'column_id': 'Change (%)'}, 'color': 'red'},
                {'if': {'filter_query': '{Change (%)} > 0', 'column_id': 'Change (%)'}, 'color': 'green'}
            ]
        )
        
        return total_value, portfolio_dv01, portfolio_duration, portfolio_convexity, executive_summary, bond_table, fig, scenario_table
    return app

if __name__ == '__main__':
    app=create_app()
    import os
    port = int(os.environ.get('PORT',5001))
    app.run(debug=False, host='0.0.0.0',port=port)
 
