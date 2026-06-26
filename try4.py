import pandas as pd
import streamlit as st
import plotly.express as px
import requests

def uploadFile():
    upload = st.file_uploader("Upload file", type=['xlsx'])
    if upload:
        try:
            df = pd.read_excel(upload, header=3)
            if not df.empty and str(df.iloc[-1]['Employee Name']).strip().lower() == 'total':
                df = df.iloc[:-1]

            
            pattern = r'^\s*(-|None|none|NONE)\s*$'
            # na = [pattern, pd.NA]
            df = df.replace(pattern, 0, regex=True)
            df.iloc[-1] = df.iloc[-1].fillna(0)

            return df
        except Exception as e:
            st.error('Error processing file - {}'.format(e))
    else:
        st.info('Please Upload file to analyse')

def dataPreview(df):
    st.subheader('Data Preview')
    st.dataframe(
        df,
        width='stretch'
    )

def productMixContri(df):
    df['Employee Name'] = df['Employee Name'].astype(str)
    
    revenue_cols = ['Brokerage', 'Unlisted Share', 'Insurance', 'Wealth']
    product_totals = df[revenue_cols].sum().reset_index()
    product_totals.columns = ['Product Line', 'Total Revenue']

    grand_total = product_totals['Total Revenue'].sum()
    product_totals['Contribution%'] = (product_totals['Total Revenue'] / grand_total * 100).round(2)

    col1, col2 = st.columns([1,2])

    with col1:
        st.subheader('Product Mix Summary')

        fig = st.dataframe(
            product_totals.style.format({'Total Revenue': '₹{:.2f}', 'Contribution%':'{:.2f}%'}),
            width='stretch',
            hide_index=True
        )
    
    with col2:
        st.subheader('Revenue share by Product Line')

        fig = px.pie(
            product_totals,
            values='Total Revenue',
            names='Product Line',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')

    st.subheader('Product Revenue split per Employee')
    #---------------------------------------------------------------------------------------------------------------------------------------
    st.write(df[["Employee Name"] + revenue_cols].head())
    st.write(df.columns.tolist())

    fig_bar = px.bar(
        df,
        x=df["Employee Name"].astype(str),
        y=revenue_cols,
        title='Revenue Distribution Across Team members',
        labels={'value':'Revenue Generated', 'variable':'Product Type'},
        barmode='stack'
    )

    # fig_bar.update_layout(
    #     bargap=0.2,
    #     xaxis={'type':'category'},
    #     height=500
    # )
    st.plotly_chart(fig_bar, use_container_width=True)

    return product_totals, revenue_cols

def toppers(df, product_totals, revenue_cols):
    sorted_products = product_totals.sort_values(by='Total Revenue').reset_index(drop=True)

    lowest_product = sorted_products.iloc[0]['Product Line']
    lowest_revenue = sorted_products.iloc[0]['Total Revenue']

    highest_product = sorted_products.iloc[-1]['Product Line']
    highest_revenue = sorted_products.iloc[-1]['Total Revenue']

    topper_emp = []

    for col in revenue_cols:
        if not df.empty and df[col].max() > 0:
            idx_max = df[col].idxmax()
            top_emp = df.loc[idx_max, 'Employee Name']
            max_val = df.loc[idx_max, col]
            topper_emp.append(
                {'Product':col, 'Top Employee': top_emp, 'Revenue':max_val}
            )
        else:
            topper_emp.append(
                {'Product':col, 'Top Employee': "No Sales", 'Revenue':0.0}
            )
    
    df_top_performers = pd.DataFrame(topper_emp)

    st.subheader("Revenue highlights and Product Champions")

    col1, col2 = st.columns([1,2])

    with col1:
        st.metric(
            label='Highest Revenue Product',
            value=highest_product,
            delta=f"₹{highest_revenue:,.2f}",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="Lowest Revenue Product",
            value=lowest_product,
            delta=f"₹{lowest_revenue:,.2f}",
            delta_color="inverse"
        )

    st.subheader("Product-wise Top Earners")
    st.dataframe(
        df_top_performers.style.format({'Revenue':"{:.2f}"}),
        width='stretch',
        hide_index=True
    )

def aum_pool_highlights(df):

    aum_cols = ['AUMC', 'MF AUM', 'Debt AUM', 'Advisory AUM', 'PMS AUM', 'AIF AUM']
    aum_totals = df[aum_cols].sum().reset_index()
    aum_totals.columns = ['AUM Type', 'Total Assets']
    sorted_aum = aum_totals.sort_values(by='Total Assets').reset_index(drop=True)

    col1, col2 = st.columns(2)
    col1.metric('Core Asset Driver', sorted_aum.iloc[-1]['AUM Type'], f"{sorted_aum.iloc[-1]['Total Assets']:,.2f}")
    col2.metric('Smallest Asset Class', sorted_aum.iloc[0]['AUM Type'], f"{sorted_aum.iloc[0]['Total Assets']:,.2f}")

    # vcol1, vcol2 = st.columns([1,1])

    # with vcol1:
    st.subheader('AUM Asset Split')
    fig_aum_bar = px.bar(
        aum_totals,
        x='AUM Type',
        y='Total Assets',
        text_auto='.2s',
        color='AUM Type',
        color_discrete_sequence=px.colors.qualitative.Prism
    )

    st.plotly_chart(fig_aum_bar, width='stretch')

    # with vcol2:
    st.subheader('Team wise Portfolio Distribution')
    fig_team_aum = px.bar(
        df,
        x='Employee Name',
        y=['AUMC', 'MF AUM', 'Debt AUM', 'Advisory AUM', 'PMS AUM', 'AIF AUM'],
        title='AUM Slicing per Employee',
        labels={"value": "Asset Value", "variable": "AUM Type"},
        barmode='stack'
    )

    st.plotly_chart(fig_team_aum, width='stretch')


# def wrap_name(name):
#     words = str(name).split()
#     if len(words)>2:
#         return "<br".join([" ".join(words[:2]), " ".join(words[2:])])
#     return name

def employee_analytics(df):

    revenue_cols = ['Brokerage', 'Unlisted Share', 'Insurance', 'Wealth']
    aum_cols = ['AUMC', 'MF AUM', 'Debt AUM', 'Advisory AUM', 'PMS AUM', 'AIF AUM']

    for col in revenue_cols + aum_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Total Income Generated'] = df[revenue_cols].sum(axis=1)
    df['Total AUM Managed'] = df[aum_cols].sum(axis=1)
    # df["Total AUM Managed"] = (pd.to_numeric(df["Total AUM Managed"], errors="coerce").fillna(0))

    st.header('Employee Productivity and Sales')

    st.subheader('Productivity Ranking (Top & Bottom earners)')

    rank_metric = st.radio(
        "Rank Employees By:",
        options=["Total Income Generated", "Total AUM Managed"],
        horizontal=True
    )

    df_sorted_emp = df.sort_values(by=rank_metric, ascending=True)

    fig_rank = px.bar(
        df_sorted_emp,
        x=rank_metric,
        y='Employee Name',
        orientation='h',
        text=rank_metric,
        title=f"Employee Productivity Ranked by {rank_metric}",
        color=rank_metric,
        color_continuous_scale=px.colors.sequential.Viridis
    )

    fig_rank.update_traces(texttemplate='%{text}', textposition='outside')
    
    st.plotly_chart(fig_rank, width='stretch')

    st.subheader('Cross Selling Efficiency Analysis')

    idx_top_earner = df['Total Income Generated'].idxmax()
    top_earner_name = df.loc[idx_top_earner, 'Employee Name']

    zero_earners = df[df['Total Income Generated'] == 0]['Employee Name'].tolist()

    if len(zero_earners)>0:
        zero_earners_text = ", ".join(map(str, zero_earners))
    else:
        zero_earners_text = "None"

    df['KYC'] = pd.to_numeric(df['KYC'], errors='coerce').fillna(0)

    df.insert(len(df.columns), 'Conversion_Ratio', df['Total Income Generated'] / (df['KYC'] + 1e-5))

    # df['Conversion_Ratio'] = df['Total Income Generated'] / (df['KYC'] + 1e-5)
    
    idx_top_cross_seller = df['Conversion_Ratio'].idxmax()
    top_cross_seller_name = df.loc[idx_top_cross_seller, 'Employee Name']

    # col1, col2 = st.columns([2,1])

    # df['Display Name'] = df['Employee Name'].apply(wrap_name)
    # text_positions = []
    # zero_revenue_counter = 0
    # positions_pool = ['top center', 'bottom center', 'middle left', 'middle right']

    # for idx, row in df.iterrows():
    #     if row['Total Income Generated'] <= 0.5 and row['KYC'] <= 1:
    #         text_positions.append(positions_pool[zero_revenue_counter % len(positions_pool)])
    #         zero_revenue_counter += 1
    #     else:
    #         text_positions.append('top center')

    coords_count = {}
    for idx, row in df.iterrows():
        x_val, y_val = float(row['KYC']), float(row['Total Income Generated'])
        coords_count[(x_val, y_val)] = coords_count.get((x_val, y_val), []) + [idx]

    display_texts = [""] * len(df)
    text_positions = ["top center"] * len(df)

    for (x_val, y_val), indices in coords_count.items():
        if len(indices) > 1:
            names_at_spot = [df.loc[i, 'Employee Name'] for i in indices]
            merged_text = "<br>".join(names_at_spot)

            display_texts[indices[0]] = merged_text
            text_positions[indices[0]] = "top center" if y_val > 0 else "bottom center"

            for extra_idx in indices[1:]:
                display_texts[extra_idx] = ""
        
        else:
            display_texts[indices[0]] = df.loc[indices[0], 'Employee Name']
            text_positions[indices[0]] = "top center"

    df["Merged_Display_Name"] = display_texts

    # with col1:
    fig_scatter = px.scatter(
        df,
        x="KYC",
        y="Total Income Generated",
        size=df["Total AUM Managed"].to_numpy(),
        hover_name="Employee Name",
        text="Merged_Display_Name",
        title="KYC Onboarding Interactions vs Total Revenue Realised",
        labels={"KYC Onboarding Count":"Customer Interactions (KYCs completed)", "Total Income Generated":"Revenue / Income Earned"},
        size_max=40
    )

    fig_scatter.update_traces(
        textposition=text_positions,
        textfont=dict(size=9, color="white"),
        marker=dict(
            color="#ae23ff",
            opacity=0.9,
            line=dict(width=1.5, color="#0b2e4f")
            ),
            hovertemplate="<b>%{hovertext}</b><br>KYC: %{x}<br>Revenue: ₹%{y:,.2f}<extra></extra>"
        )
    
    fig_scatter.update_layout(
        height=650,
        yaxis=dict(range=[-4, df['Total Income Generated'].max() + 3]),
        xaxis=dict(range=[-1, df['KYC'].max() + 1]),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig_scatter, width='stretch')

    # with col2:
    st.markdown("**Cross-Selling Observations**")
    st.info(
        f"**High Efficiency Leader:** **{top_cross_seller_name}** maps the highest revenue conversion per "
        f"onboarding interation, proving strong cross-selling success."
    )

    st.warning(
        f"**Top Overall Contributor:** **{top_earner_name}** is leading the workspace in gross income generation"
    )

    if zero_earners:
        st.error(
            f"**Attention required:** The following employees show zero revenue pipeline movement this quarter: "
            f"**{zero_earners_text}**. This indicates operational onboarding friction or a complete cross-selling stall."
        )

def download_file():
    url1 = "https://github.com/Raj280901/mis-dashboard/raw/refs/heads/main/Book15.xlsx"
    response = requests.get(url1)
    if response.status_code == 200:
        return response.content
    else:
        st.error("Failed to fetch demo file")
        return None


def tabs(df):
    tab1, tab2 = st.tabs(["Products", "AUM"])
    with tab1:
        dataPreview(df)
        product_totals, revenue_cols = productMixContri(df)
        toppers(df, product_totals, revenue_cols)
    with tab2:
        dataPreview(df)
        aum_pool_highlights(df)

def page_setp():
    st.set_page_config(layout='wide')
    st.html(
        """
            <style>
                .block-container {
                    padding-left: 15rem !important;
                    padding-right: 15rem !important;
                
                }

            </style>
        """
    )


st.write("Hello")

st.write("***In case you don't have a file to test ->***")

file_data = download_file()
if file_data:
    st.download_button(
        label="Download Demo MIS file",
        data=file_data,
        file_name="MIS.xlsx",
        mime="text/xlsx"
    )

page_setp()
df = uploadFile()
if df is not None:
    tabs(df)
    st.divider()
    employee_analytics(df)


