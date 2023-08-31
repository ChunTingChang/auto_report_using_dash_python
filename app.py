
# coding: utf-8

# In[ ]:

import dash_core_components as dcc
import dash_html_components as html
# import dash as html
# import dash as dcc
from dash_table.Format import Format

import pandas as pd

import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import callback_context, Dash
# Determining which Button Changed with callback_context: https://dash.plotly.com/dash-html-components/button

import time
import datetime

import dash_table
import dash_auth


# In[ ]:

# read in client details raw data

contract_details = pd.read_csv(r'resources/partner_details.csv')
contract_details['Extra Cost (Contract Currency)'] = 0
contract_details = contract_details.rename(columns = {
    'client': 'Client',
    'currency': 'Contract Currency',
    'fixed_exchange_rate': 'FX',
    'fee_structure': 'Fee Structure'
})


# In[ ]:

# format datatable columns for client details

client_col = ['Client', 'Contract Currency', 'FX', 'Fee Structure', 'Extra Cost (Contract Currency)']

client_columns = []

for i in client_col:

    if i == 'Client':
        tmp = {"name": i,
                 "id": i,
                 'type': 'text'}

    elif 'Currency' in i:
        tmp = {"name": i,
                 "id": i,
                 'type': 'text'}

    else:
        tmp = {"name": i,
            "id": i,
            'type': 'numeric',
              }

    client_columns.append(tmp)

col = ['Client',
       'Revenue (£)',
       'Fee Structure',
       'Commission Due before Extra Cost (£)',
       'Contract Currency',
       'FX',
       'Extra Cost (Contract Currency)',
       'Commission Due (Contract Currency)',
       'Commission Due (£)'
      ]

columns = []

# format datatable columns for finance report

for i in col:

    if i == 'Client':
        tmp = {"name": i,
                 "id": i,
                 'type': 'text'}

    elif ('£' in i) :
        tmp = {"name": i,
            "id": i,
            'type': 'numeric',
            'format':
               {
                'locale': {
                    'symbol': ['£', '']
                },
                'specifier': '$,.2f'
            }
              }

    elif i == 'Extra Cost (Contract Currency)':

        tmp = {"name": i,
            "id": i,
            'type': 'numeric',
            'format':
               {
                'specifier': ',.2f'
            }
              }

    elif ('Commission' in i) | ('Extra Cost' in i):
        tmp = {"name": i,
            "id": i,
            'type': 'numeric',
            'format':
               {
                'specifier': ',.2f'
            }
              }

    else:
        tmp = {"name": i,
            "id": i,
            'type': 'numeric',
            'format': Format(group=',')}

    columns.append(tmp)


# In[ ]:

# auth

user_login_info = {
    'test': 'test',
}


# In[ ]:

app = Dash(__name__)


# auth
auth = dash_auth.BasicAuth(
    app,
    user_login_info
)

server = app.server


# In[ ]:

def get_fn_data(start_date, end_date, internal, editables):

    df = pd.read_csv(r'resources/finance_data.csv')
    df['processed_date'] = pd.to_datetime(df.processed_date).dt.date

# add 1d for end_date to include whole day of end_date

    end_date = (pd.to_datetime(end_date) + datetime.timedelta(days = 1)).date()

    trim_df = df[(df.processed_date <= pd.to_datetime(end_date).date()) & (df.processed_date >= pd.to_datetime(start_date).date())]

# identify internal/ external client

    if internal == 'ex':
        client_df = contract_details[contract_details.is_internal == False]
    elif internal == 'in':
        client_df = contract_details[contract_details.is_internal == True]
    elif internal == 'all':
        client_df = contract_details

    merge_df = trim_df.merge(client_df, left_on = 'client', right_on = 'Client', how = 'inner')

    finance_df = pd.pivot_table(data = merge_df,
                        index = 'Client',
                        values = 'revenue',
                        aggfunc = {'revenue': 'sum'}
                       ).reset_index().rename(columns = {'revenue': 'Revenue (£)'})

    finance_df = finance_df.merge(editables,
                          left_on = 'Client',
                          right_on = 'Client',
                          how = 'left')

    finance_df = finance_df.fillna(0)
    finance_df['Commission Due before Extra Cost (£)'] = finance_df['Revenue (£)'] * finance_df['Fee Structure']
    finance_df['Extra Cost (Contract Currency)'] = finance_df['Extra Cost (Contract Currency)'].astype(float)
    finance_df['Commission Due (Contract Currency)'] = finance_df['Commission Due before Extra Cost (£)'] * finance_df['FX'] - finance_df['Extra Cost (Contract Currency)']
    finance_df['Commission Due (£)'] = finance_df['Commission Due (Contract Currency)'] / finance_df['FX']

    finance_df = finance_df.fillna(0)

# save data in dict type (in order to input into dash-datatable)
    data = finance_df.to_dict('records')

    return data


# In[ ]:

def update_on_page_load():

#     pre-load client details table

    client_data = (contract_details[['Client',
                                      'Contract Currency',
                                      'FX',
                                      'Fee Structure',
                                      'Extra Cost (Contract Currency)']]).to_dict('records')

    return html.Div(
    className = 'page',
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Company Financial Performance",
                    style={
                        "textAlign": "left"
                          },
                ),

                html.Div(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Dropdown(
                                    id="client_picker",
                                    options=[
                                        {"label": "External Clients", "value": "ex"},
                                        {"label": "Internal Clients", "value": "in"},
                                        {"label": "All Clients", "value": "all"},
                                    ],
                                    value="ex",
                                    style={'height': '47px', 'align-items': 'center', 'justify-content': 'center', 'textAlign': 'left'}
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dcc.DatePickerRange(
                                    id="date_picker_range",
                                    with_portal=True,
                                    clearable=True,
#                                     limit the date range
                                    min_date_allowed=(datetime.date(2021,10,15)),
                                    max_date_allowed=(datetime.date(2021,10,24)),
                                    initial_visible_month=(
                                        datetime.date.today()
                                        - datetime.timedelta(days=1)
                                    ),
                                    display_format="Y-MM-DD",
                                    start_date_placeholder_text="YYYY-MM-DD",
                                    updatemode="singledate",
                                    end_date=(datetime.date(2021,10,23)),
                                )
                            ),
                        ],
                    )
                ),

                html.Div(
                    className="submit",
                    children=[
                        dbc.Button(
                            "Submit",
                            outline=True,
                            color="primary",
                            id="submit",
                            n_clicks=0

                        ),
                    ],
                ),

                html.H4(children="Client Details & Extra Cost"),
                html.Div(
                    [
                        dbc.Button(
                            "Open collapse",
                            id="collapse-button",
                            className="mb-3",
                            color="primary",
                            n_clicks=0,
                        ),
                        dbc.Collapse(
                            html.Div(
                                [
                                    dbc.Card(
                                        dbc.CardBody(
                                            "Please provide `Extra Cost` if there is any during selceted period. Otherwise, it's okay to leave it 0."
                                        )
                                    ),
                                    dash_table.DataTable(

                                        id="client_contact_details",
                                        columns=client_columns,
                                        data=client_data,
                                        editable=True,
                                        filter_action="native",
                                        sort_action="native",
                                        sort_mode="multi",
                                        row_deletable=False,
                                        page_action="native",
                                        page_current=0,
                                        page_size=10,
                                        style_table={
                                            "overflowX": "auto",
                                            "padding": "15px",
                                        },
                                        style_cell={
                                            "padding": "5px",
                                            "height": "auto",
                                            "minWidth": "180px",
                                            "width": "180px",
                                            "maxWidth": "180px",  # all three widths are needed
                                            "whiteSpace": "normal",
                                        },
                                        export_format="xlsx",
                                        export_headers="display",

                                    ),
                                ]
                            ),
                            id="collapse",
                            is_open=False,
                        ),
                    ]
                ),
                html.Br(),
                html.Br(),
                html.Hr(),
                html.H4(children="Finance Report"),
                html.Div(
                    [
                        dbc.Spinner(
                            dash_table.DataTable(
                                id="fn_data",
                                columns=columns,
                                data=[],
                                sort_action="native",
                                sort_mode="multi",
                                column_selectable="multi",
                                row_deletable=False,
                                selected_columns=[],
                                page_action="native",
                                page_current=0,
                                page_size=10,
                                style_table={"overflowX": "auto", "padding": "15px"},
                                style_cell={
                                    "padding": "5px",
                                    "height": "auto",
                                    "minWidth": "120px",
                                    "width": "120px",
                                    "maxWidth": "180px",  # all three widths are needed
                                    "whiteSpace": "normal",
                                },
                                export_format="xlsx",
                                export_headers="display",

                            ),
                            color="primary"
                        ),
                        dcc.Store(id='previous_fn_data') # save previously-submitted data
                    ]
                ),
                html.Br(),
                html.Br(),
            ],
            style={
                "marginBottom": 10,
                "marginTop": 25,
                "marginLeft": 50,
                "marginRight": 50,
            },
        ),
    ]
)


app.layout = update_on_page_load

# save previously-submitted data
# dcc.Store() https://dash.plotly.com/sharing-data-between-callbacks

@app.callback(
    [Output('previous_fn_data', 'data')],
    [Input('fn_data', 'data')]
)

def save_data(data):

    return [data]

# take values in filters and client details table to update finance report

@app.callback(
    [Output('fn_data', 'data')],
    [Input('submit', 'n_clicks'),
     Input('date_picker_range', 'start_date'),
     Input('date_picker_range', 'end_date'),
     Input('client_picker', 'value'),
     Input('client_contact_details', 'data'),
     Input('client_contact_details', 'columns'),
     Input('previous_fn_data', 'data')
    ])

def get_data(submit, start_date, end_date, partner, partner_data, partner_cols, previous_data):

#     `changed_id` = get the latest action
    changed_id = [action['prop_id'] for action in callback_context.triggered][0]

    if ('submit' in changed_id) & (start_date != None) & (end_date != None) & (partner != None):

        partner_edit = pd.DataFrame(partner_data, columns=[c['name'] for c in partner_cols])
        data = get_fn_data(start_date, end_date, partner, partner_edit)

        return [data]

    elif changed_id == '.':

        df = pd.DataFrame()
        data = df.to_dict('records')

        return [data]

    else:

        if previous_data == []: # if never submit, show an empty table

            df = pd.DataFrame()
            data = df.to_dict('records')

            return [data]

        else: # if user has submitted before, show previously-submitted data (until next submission)

            return [previous_data]

# collapse function

@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=False)


# In[ ]:
