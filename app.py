import datetime
import io
import logging
from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

logging.basicConfig(level=logging.INFO)

STRATEGY_COLOR = '#1F4E79'
BUY_HOLD_COLOR = '#000000'
DRAWDOWN_COLOR = '#6E6E6E'
COST_COLOR = '#A0A0A0'
SLIPPAGE_COLOR = '#4F4F4F'


def set_page_style() -> None:
    st.set_page_config(page_title='Backtesting Bias Analysis', layout='wide')
    st.markdown(
        '''
        <style>
            html, body, [data-testid='stAppViewContainer'] {
                background: #2a2a2a;
                color: #e0e0e0;
                font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
            .css-18e3th9 {padding-top: 0rem;}
            .css-1d391kg {padding: 1rem 1rem 0 1rem;}
            .css-1avcm0n, .css-1aumxhk {
                background-color: #2a2a2a;
            }
            .stSidebar .css-1d391kg {
                background-color: #1f1f1f;
            }
            .stButton>button {
                background-color: #1F4E79;
                color: #ffffff;
                border: 1px solid #1F4E79;
                border-radius: 4px;
                font-weight: 600;
            }
            .stButton>button:hover {
                background-color: #163f63;
            }
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
                color: #ffffff;
                margin-bottom: 0.25rem;
            }
            .stMarkdown p, .stMarkdown li {
                color: #d0d0d0;
                font-size: 14px;
                line-height: 1.6;
            }
            .stDataFrame td, .stDataFrame th, .streamlit-expanderHeader {
                color: #e0e0e0;
            }
            .stMetric > div {
                padding: 0.9rem 0.75rem;
            }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def base_plot_layout(title: str = None) -> dict:
    layout = {
        'template': 'plotly_dark',
        'font': {'family': 'Inter, Arial, sans-serif', 'color': '#e0e0e0', 'size': 12},
        'paper_bgcolor': '#2a2a2a',
        'plot_bgcolor': '#2a2a2a',
        'xaxis': {
            'showgrid': True,
            'gridcolor': '#404040',
            'zeroline': False,
            'showline': True,
            'linecolor': '#505050',
            'ticks': 'outside',
            'tickcolor': '#b0b0b0',
            'tickfont': {'size': 11, 'color': '#c0c0c0'},
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': "#361B1B",
            'zeroline': False,
            'showline': True,
            'linecolor': '#505050',
            'ticks': 'outside',
            'tickcolor': '#b0b0b0',
            'tickfont': {'size': 11, 'color': '#c0c0c0'},
        },
        'legend': {
            'bordercolor': '#505050',
            'borderwidth': 1,
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1.0,
            'font': {'size': 11, 'color': '#e0e0e0'},
        },
        'margin': {'l': 40, 'r': 20, 't': 60, 'b': 40},
        'hovermode': 'x unified',
    }
    if title:
        layout['title'] = {'text': title, 'x': 0.01, 'xanchor': 'left', 'font': {'size': 18, 'color': '#ffffff'}}
    return layout


@st.cache_data(show_spinner=False)
def download_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    symbol = ticker.strip().upper()
    df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f'No data returned for {symbol}.')
    df = df.loc[~df.index.duplicated(keep='first')]
    return df[['Close']].rename(columns={'Close': 'price'})


def compute_sma_signals(data: pd.DataFrame, fast_window: int, slow_window: int) -> pd.DataFrame:
    df = data.copy()
    df['sma_fast'] = df['price'].rolling(fast_window, min_periods=fast_window).mean()
    df['sma_slow'] = df['price'].rolling(slow_window, min_periods=slow_window).mean()
    df['signal'] = 0
    df.loc[df['sma_fast'] > df['sma_slow'], 'signal'] = 1
    df['signal'] = df['signal'].astype(int)
    df['signal_correct'] = df['signal'].shift(1).fillna(0).astype(int)
    df['returns'] = df['price'].pct_change().fillna(0)
    return df


def apply_costs(returns: pd.Series, positions: pd.Series, transaction_cost_pct: float, slippage_pct: float) -> pd.Series:
    trades = positions.diff().abs().fillna(0)
    cost_rate = transaction_cost_pct / 100.0
    slip_rate = slippage_pct / 100.0
    costs = trades * (cost_rate + slip_rate)
    return positions * returns - costs


def create_equity_curve(returns: pd.Series) -> pd.Series:
    return (1 + returns).cumprod()


def drawdown_series(equity: pd.Series) -> pd.Series:
    peaks = equity.cummax()
    return (equity - peaks) / peaks


def monthly_return_matrix(returns: pd.Series) -> pd.DataFrame:
    df = returns.to_frame('returns').copy()
    df['year'] = df.index.year
    df['month'] = df.index.month_name().str[:3]
    pivot = df.pivot_table(index='year', columns='month', values='returns', aggfunc='sum').fillna(0)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot = pivot.reindex(columns=months)
    return pivot.sort_index()


def performance_metrics(equity: pd.Series, returns: pd.Series) -> dict:
    duration = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    annualized_vol = returns.std() * np.sqrt(252)
    cagr = (1 + total_return) ** (1 / duration) - 1
    sharpe = cagr / annualized_vol if annualized_vol > 0 else np.nan
    max_drawdown = drawdown_series(equity).min()
    return {
        'Total Return': total_return,
        'CAGR': cagr,
        'Sharpe Ratio': sharpe,
        'Maximum Drawdown': max_drawdown,
        'Number of Trades': int((returns != 0).sum()),
        'Market Exposure': float((returns != 0).mean()),
    }


def format_percentage(value: float) -> str:
    if pd.isna(value):
        return 'n/a'
    return f'{value:.2%}'


def format_decimal(value: float) -> str:
    if pd.isna(value):
        return 'n/a'
    return f'{value:.2f}'


def render_kpis(metrics: dict) -> None:
    labels = ['Total Return', 'CAGR', 'Sharpe Ratio', 'Maximum Drawdown', 'Number of Trades', 'Market Exposure']
    columns = st.columns(6)
    for label, col in zip(labels, columns):
        value = metrics.get(label, np.nan)
        if label == 'Number of Trades':
            display = f'{int(value):,}' if not pd.isna(value) else 'n/a'
        else:
            display = format_percentage(value)
        col.metric(label, display)


def build_trade_log(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    trades = df[df['signal_correct'].diff().fillna(0) != 0].copy()
    trades['Action'] = np.where(trades['signal_correct'] == 1, 'Entry', 'Exit')
    trades = trades[['Action', 'price']].rename(columns={'price': 'Execution Price'})
    trades.index.name = 'Date'
    trades = trades.reset_index()
    trades['Execution Price'] = trades['Execution Price'].map('${:,.2f}'.format)
    return trades.tail(limit).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def run_strategy_backtest(
    price_data: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    transaction_cost_pct: float,
    slippage_pct: float,
) -> dict:
    if slow_window <= fast_window:
        raise ValueError('Slow SMA must be larger than fast SMA.')
    df = compute_sma_signals(price_data, fast_window, slow_window)
    df['strategy_returns'] = apply_costs(df['returns'], df['signal_correct'], transaction_cost_pct, slippage_pct)
    df['buy_hold_returns'] = df['returns']
    df['lookahead_returns'] = apply_costs(df['returns'], df['signal'], transaction_cost_pct, slippage_pct)
    df['equity_strategy'] = create_equity_curve(df['strategy_returns'])
    df['equity_buy_hold'] = create_equity_curve(df['buy_hold_returns'])
    df['equity_lookahead'] = create_equity_curve(df['lookahead_returns'])
    df['drawdown_strategy'] = drawdown_series(df['equity_strategy'])
    return {
        'df': df,
        'metrics_strategy': performance_metrics(df['equity_strategy'], df['strategy_returns']),
        'metrics_buy_hold': performance_metrics(df['equity_buy_hold'], df['buy_hold_returns']),
        'metrics_lookahead': performance_metrics(df['equity_lookahead'], df['lookahead_returns']),
        'monthly_heatmap': monthly_return_matrix(df['strategy_returns']),
        'trade_log': build_trade_log(df),
    }


@st.cache_data(show_spinner=False)
def run_survivorship_comparison(tickers: List[str], fast_window: int, slow_window: int, start_date: str, end_date: str) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        try:
            prices = download_data(ticker, start_date, end_date)
            result = run_strategy_backtest(prices, fast_window, slow_window, 0.0, 0.0)
            metrics = result['metrics_strategy']
            rows.append({
                'Ticker': ticker,
                'Total Return': metrics['Total Return'],
                'Sharpe Ratio': metrics['Sharpe Ratio'],
                'Maximum Drawdown': metrics['Maximum Drawdown'],
            })
        except Exception:
            rows.append({'Ticker': ticker, 'Total Return': np.nan, 'Sharpe Ratio': np.nan, 'Maximum Drawdown': np.nan})
    return pd.DataFrame(rows).set_index('Ticker')


@st.cache_data(show_spinner=False)
def optimize_sma_parameters(price_data: pd.DataFrame, fast_range: List[int], slow_range: List[int]) -> pd.DataFrame:
    records = []
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            try:
                result = run_strategy_backtest(price_data, fast, slow, 0.0, 0.0)
                metrics = result['metrics_strategy']
                records.append({'fast': fast, 'slow': slow, 'total_return': metrics['Total Return'], 'sharpe': metrics['Sharpe Ratio']})
            except Exception:
                continue
    return pd.DataFrame(records)


def plot_equity_curve(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['equity_strategy'], mode='lines', name='Strategy', line=dict(color=STRATEGY_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['equity_buy_hold'], mode='lines', name='Buy and Hold', line=dict(color=BUY_HOLD_COLOR, width=2, dash='dash')))
    fig.update_layout(**base_plot_layout('Equity Curve: Strategy vs Buy and Hold'))
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Equity')
    return fig


def plot_drawdown(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['drawdown_strategy'], mode='lines', name='Drawdown', line=dict(color=DRAWDOWN_COLOR, width=2), fill='tozeroy'))
    fig.update_layout(**base_plot_layout('Drawdown Profile'))
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Drawdown', tickformat='-.0%')
    return fig


def plot_monthly_heatmap(matrix: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns,
        y=matrix.index.astype(str),
        colorscale=[[0.0, '#f5f5f5'], [0.5, '#b0b0b0'], [1.0, STRATEGY_COLOR]],
        colorbar=dict(title='Monthly Return', tickformat='.0%'),
        hovertemplate='%{y} %{x}: %{z:.2%}<extra></extra>',
    ))
    fig.update_layout(**base_plot_layout('Monthly Return Heatmap'))
    fig.update_xaxes(title='Month')
    fig.update_yaxes(title='Year')
    return fig


def plot_return_distribution(returns: pd.Series) -> go.Figure:
    fig = px.histogram(
        returns.dropna(),
        nbins=35,
        labels={'value': 'Daily Return'},
        marginal='box',
        histnorm='probability density',
    )
    fig.update_traces(marker_color=STRATEGY_COLOR, opacity=0.85, marker_line_color='#333333', marker_line_width=0.5)
    fig.update_layout(**base_plot_layout('Return Distribution'))
    fig.update_xaxes(title='Daily Return', tickformat='.2%')
    fig.update_yaxes(title='Density')
    return fig


def plot_bias_equity(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['equity_strategy'], mode='lines', name='Correct Strategy', line=dict(color=STRATEGY_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['equity_lookahead'], mode='lines', name='Look-Ahead Bias', line=dict(color=SLIPPAGE_COLOR, width=2, dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['equity_buy_hold'], mode='lines', name='Buy and Hold', line=dict(color=BUY_HOLD_COLOR, width=1.5, dash='dot')))
    fig.update_layout(**base_plot_layout('Look-Ahead Bias: Equity Comparison'))
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Equity')
    return fig


def plot_survivorship_bars(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Total Return', x=df.index.astype(str), y=df['Total Return'], marker_color=STRATEGY_COLOR))
    fig.add_trace(go.Bar(name='Sharpe Ratio', x=df.index.astype(str), y=df['Sharpe Ratio'], marker_color=DRAWDOWN_COLOR))
    fig.add_trace(go.Bar(name='Maximum Drawdown', x=df.index.astype(str), y=df['Maximum Drawdown'], marker_color=BUY_HOLD_COLOR))
    fig.update_layout(barmode='group', **base_plot_layout('Survivorship Bias Comparison'))
    fig.update_xaxes(title='Ticker')
    fig.update_yaxes(title='Metric Value')
    return fig


def plot_transaction_cost_impact(baseline_df: pd.DataFrame, cost_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=baseline_df.index, y=baseline_df['equity_strategy'], mode='lines', name='Baseline', line=dict(color=STRATEGY_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=cost_df.index, y=cost_df['equity_strategy'], mode='lines', name='Transaction Costs', line=dict(color=COST_COLOR, width=2, dash='dash')))
    fig.add_trace(go.Scatter(x=baseline_df.index, y=baseline_df['equity_buy_hold'], mode='lines', name='Buy and Hold', line=dict(color=BUY_HOLD_COLOR, width=1.5, dash='dot')))
    fig.update_layout(**base_plot_layout('Transaction Cost Impact'))
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Equity')
    return fig


def plot_slippage_impact(baseline_df: pd.DataFrame, slippage_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=baseline_df.index, y=baseline_df['equity_strategy'], mode='lines', name='Baseline', line=dict(color=STRATEGY_COLOR, width=2)))
    fig.add_trace(go.Scatter(x=slippage_df.index, y=slippage_df['equity_strategy'], mode='lines', name='Costs + Slippage', line=dict(color=SLIPPAGE_COLOR, width=2, dash='dash')))
    fig.add_trace(go.Scatter(x=baseline_df.index, y=baseline_df['equity_buy_hold'], mode='lines', name='Buy and Hold', line=dict(color=BUY_HOLD_COLOR, width=1.5, dash='dot')))
    fig.update_layout(**base_plot_layout('Slippage Impact'))
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Equity')
    return fig


def plot_optimization_heatmap(result_df: pd.DataFrame) -> go.Figure:
    matrix = result_df.pivot(index='slow', columns='fast', values='total_return')
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns,
        y=matrix.index,
        colorscale='Greys',
        colorbar=dict(title='Return', tickformat='.0%'),
        hovertemplate='Fast: %{x}<br>Slow: %{y}<br>Return: %{z:.2%}<extra></extra>',
    ))
    fig.update_layout(**base_plot_layout('SMA Optimization Heatmap'))
    fig.update_xaxes(title='Fast SMA')
    fig.update_yaxes(title='Slow SMA')
    return fig


def plot_optimization_surface(result_df: pd.DataFrame) -> go.Figure:
    matrix = result_df.pivot(index='slow', columns='fast', values='total_return').sort_index(ascending=False)
    fig = go.Figure(data=[
        go.Surface(z=matrix.values, x=matrix.columns, y=matrix.index, colorscale='Greys', colorbar={'title': 'Return', 'tickformat': '.0%'}),
    ])
    fig.update_layout(**base_plot_layout('SMA Optimization Surface'))
    fig.update_scenes(xaxis_title='Fast SMA', yaxis_title='Slow SMA', zaxis_title='Total Return')
    return fig


def plot_optimization_scatter(result_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        result_df,
        x='sharpe',
        y='total_return',
        color='fast',
        size='slow',
        labels={'sharpe': 'Sharpe Ratio', 'total_return': 'Total Return', 'fast': 'Fast SMA', 'slow': 'Slow SMA'},
        color_continuous_scale=[STRATEGY_COLOR, DRAWDOWN_COLOR],
    )
    fig.update_layout(**base_plot_layout('Return vs Sharpe'))
    fig.update_xaxes(title='Sharpe Ratio')
    fig.update_yaxes(title='Total Return', tickformat='.0%')
    return fig


def render_research_section(title: str, objective: str, methodology: str, results: str, interpretation: str) -> None:
    st.subheader(title)
    st.markdown(f'**Objective:** {objective}')
    st.markdown(f'**Methodology:** {methodology}')
    st.markdown(f'**Results:** {results}')
    st.markdown(f'**Interpretation:** {interpretation}')


def main() -> None:
    set_page_style()
    st.title('Backtesting Bias Analysis')
    st.markdown('Institutional research dashboard for SMA crossover bias diagnostics and execution-aware backtesting.')

    if 'run_requested' not in st.session_state:
        st.session_state.run_requested = False

    with st.sidebar.form(key='analysis_inputs'):
        ticker = st.text_input('Ticker symbol', value='SPY').upper()
        start_date = st.date_input('Start date', value=datetime.date(2020, 1, 1))
        end_date = st.date_input('End date', value=datetime.date.today())
        fast_window = st.number_input('Fast SMA window', min_value=5, max_value=200, value=50, step=1)
        slow_window = st.number_input('Slow SMA window', min_value=10, max_value=400, value=200, step=1)
        transaction_cost_pct = st.number_input('Transaction cost (%)', min_value=0.0, max_value=5.0, value=0.10, step=0.01, format='%.2f')
        slippage_pct = st.number_input('Slippage (%)', min_value=0.0, max_value=5.0, value=0.05, step=0.01, format='%.2f')
        st.markdown('---')
        st.markdown('**Bias diagnostics available:**')
        st.markdown('- Look-Ahead Bias\n- Survivorship Bias\n- Transaction Costs\n- Slippage')
        run_button = st.form_submit_button('Run Analysis')

    if run_button:
        st.session_state.run_requested = True

    if not st.session_state.run_requested:
        st.info('Enter ticker, dates, SMA windows, and friction parameters in the sidebar. Then run the analysis to populate the dashboard.')
        return

    if slow_window <= fast_window:
        st.error('Slow SMA must be larger than Fast SMA.')
        return

    try:
        price_data = download_data(ticker, start_date.isoformat(), end_date.isoformat())
    except Exception as error:
        st.error(f'Unable to load data for {ticker}: {error}')
        return

    baseline = run_strategy_backtest(price_data, fast_window, slow_window, transaction_cost_pct, slippage_pct)
    buy_hold_metrics = baseline['metrics_buy_hold']

    tabs = st.tabs(['Strategy', 'Bias Analysis', 'Optimization', 'Research Notes'])

    with tabs[0]:
        st.header('Strategy')
        st.markdown(
            'The SMA crossover strategy is executed with a one-day lag on the signal to avoid look-ahead bias. Performance is shown net of the selected transaction costs and slippage assumptions.'
        )
        render_kpis(baseline['metrics_strategy'])

        st.plotly_chart(plot_equity_curve(baseline['df']), use_container_width=True)

        chart_col, summary_col = st.columns([2, 1])
        with chart_col:
            st.plotly_chart(plot_drawdown(baseline['df']), use_container_width=True)
            st.plotly_chart(plot_return_distribution(baseline['df']['strategy_returns']), use_container_width=True)
        with summary_col:
            st.plotly_chart(plot_monthly_heatmap(baseline['monthly_heatmap']), use_container_width=True)
            st.markdown('**Benchmark comparison**')
            benchmark = pd.DataFrame(
                {
                    'SMA Strategy': {
                        'Total Return': format_percentage(baseline['metrics_strategy']['Total Return']),
                        'CAGR': format_percentage(baseline['metrics_strategy']['CAGR']),
                        'Sharpe Ratio': format_decimal(baseline['metrics_strategy']['Sharpe Ratio']),
                        'Max Drawdown': format_percentage(baseline['metrics_strategy']['Maximum Drawdown']),
                    },
                    'Buy and Hold': {
                        'Total Return': format_percentage(buy_hold_metrics['Total Return']),
                        'CAGR': format_percentage(buy_hold_metrics['CAGR']),
                        'Sharpe Ratio': format_decimal(buy_hold_metrics['Sharpe Ratio']),
                        'Max Drawdown': format_percentage(buy_hold_metrics['Maximum Drawdown']),
                    },
                }
            )
            st.table(benchmark)

        st.markdown('#### Recent trade sample')
        st.table(baseline['trade_log'])

    with tabs[1]:
        st.header('Bias Analysis')
        bias_choice = st.selectbox('Select bias focus', ['Look-Ahead Bias', 'Survivorship Bias', 'Transaction Costs', 'Slippage'])

        if bias_choice == 'Look-Ahead Bias':
            st.markdown(
                'Look-ahead bias in backtesting occurs when signals use information from the future. The chart below compares the correct delayed signal to the look-ahead variant.'
            )
            st.plotly_chart(plot_bias_equity(baseline['df']), use_container_width=True)
            bias_table = pd.DataFrame(
                {
                    'Correct Strategy': {
                        'Total Return': format_percentage(baseline['metrics_strategy']['Total Return']),
                        'Sharpe Ratio': format_decimal(baseline['metrics_strategy']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(baseline['metrics_strategy']['Maximum Drawdown']),
                    },
                    'Look-Ahead Bias': {
                        'Total Return': format_percentage(baseline['metrics_lookahead']['Total Return']),
                        'Sharpe Ratio': format_decimal(baseline['metrics_lookahead']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(baseline['metrics_lookahead']['Maximum Drawdown']),
                    },
                    'Buy and Hold': {
                        'Total Return': format_percentage(buy_hold_metrics['Total Return']),
                        'Sharpe Ratio': format_decimal(buy_hold_metrics['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(buy_hold_metrics['Maximum Drawdown']),
                    },
                }
            )
            st.table(bias_table)

        elif bias_choice == 'Survivorship Bias':
            st.markdown(
                'Survivorship bias appears when historical analysis only includes assets that remain in the universe today. This comparison highlights the effect across a small sample.'
            )
            universe = ['SPY', 'AAPL', 'XOM', 'GE']
            survivor_results = run_survivorship_comparison(universe, fast_window, slow_window, start_date.isoformat(), end_date.isoformat())
            st.table(survivor_results.applymap(lambda v: format_percentage(v) if isinstance(v, (int, float, np.floating, np.integer)) else 'n/a'))
            st.plotly_chart(plot_survivorship_bars(survivor_results), use_container_width=True)

        elif bias_choice == 'Transaction Costs':
            st.markdown(
                'Transaction costs are modeled for each change in exposure. The chart below contrasts the frictionless baseline with the cost-adjusted curve.'
            )
            frictionless = run_strategy_backtest(price_data, fast_window, slow_window, 0.0, 0.0)
            cost_adjusted = run_strategy_backtest(price_data, fast_window, slow_window, transaction_cost_pct, 0.0)
            st.plotly_chart(plot_transaction_cost_impact(frictionless['df'], cost_adjusted['df']), use_container_width=True)
            table = pd.DataFrame(
                {
                    'Frictionless': {
                        'Total Return': format_percentage(frictionless['metrics_strategy']['Total Return']),
                        'Sharpe Ratio': format_decimal(frictionless['metrics_strategy']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(frictionless['metrics_strategy']['Maximum Drawdown']),
                    },
                    'With Transaction Costs': {
                        'Total Return': format_percentage(cost_adjusted['metrics_strategy']['Total Return']),
                        'Sharpe Ratio': format_decimal(cost_adjusted['metrics_strategy']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(cost_adjusted['metrics_strategy']['Maximum Drawdown']),
                    },
                }
            )
            st.table(table)

        else:
            st.markdown(
                'Slippage models the execution gap between the theoretical fill price and the realized transaction price, layered on top of explicit trading costs.'
            )
            cost_only = run_strategy_backtest(price_data, fast_window, slow_window, transaction_cost_pct, 0.0)
            cost_slippage = run_strategy_backtest(price_data, fast_window, slow_window, transaction_cost_pct, slippage_pct)
            st.plotly_chart(plot_slippage_impact(cost_only['df'], cost_slippage['df']), use_container_width=True)
            table = pd.DataFrame(
                {
                    'Transaction Costs Only': {
                        'Total Return': format_percentage(cost_only['metrics_strategy']['Total Return']),
                        'Sharpe Ratio': format_decimal(cost_only['metrics_strategy']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(cost_only['metrics_strategy']['Maximum Drawdown']),
                    },
                    'Costs + Slippage': {
                        'Total Return': format_percentage(cost_slippage['metrics_strategy']['Total Return']),
                        'Sharpe Ratio': format_decimal(cost_slippage['metrics_strategy']['Sharpe Ratio']),
                        'Maximum Drawdown': format_percentage(cost_slippage['metrics_strategy']['Maximum Drawdown']),
                    },
                }
            )
            st.table(table)

    with tabs[2]:
        st.header('Optimization')
        st.markdown(
            'A parameter sweep over the SMA windows reveals whether the best historical combinations are isolated or part of a broader response surface.'
        )
        fast_values = list(range(10, 101, 10))
        slow_values = list(range(120, 301, 20))
        optimization_df = optimize_sma_parameters(price_data, fast_values, slow_values)
        if optimization_df.empty:
            st.error('Optimization did not produce any valid parameter combinations for the selected input range.')
        else:
            st.plotly_chart(plot_optimization_heatmap(optimization_df), use_container_width=True)
            st.plotly_chart(plot_optimization_surface(optimization_df), use_container_width=True)
            top_results = optimization_df.sort_values('total_return', ascending=False).head(10).copy()
            top_results['total_return'] = top_results['total_return'].map(lambda v: format_percentage(v) if not pd.isna(v) else 'n/a')
            top_results['sharpe'] = top_results['sharpe'].map(lambda v: format_decimal(v) if not pd.isna(v) else 'n/a')
            st.markdown('#### Top 10 Parameter Combinations')
            st.table(top_results)
            st.plotly_chart(plot_optimization_scatter(optimization_df), use_container_width=True)

    with tabs[3]:
        st.header('Research Notes')
        render_research_section(
            'Baseline Strategy',
            'Assess the SMA crossover strategy using delayed execution and realistic friction assumptions.',
            'The strategy is modeled on adjusted close prices with a one-day delay to prevent look-ahead bias.',
            f'The strategy returned {format_percentage(baseline["metrics_strategy"]["Total Return"])} with a Sharpe ratio of {format_decimal(baseline["metrics_strategy"]["Sharpe Ratio"])}.',
            'This section provides a concise narrative for investment research review.',
        )
        render_research_section(
            'Look-Ahead Bias',
            'Compare correctly delayed signals to a look-ahead implementation.',
            'A look-ahead variant uses same-day signals and overstates execution performance.',
            'The look-ahead simulation shows inflated returns and lower perceived drawdowns relative to the valid delayed implementation.',
            'Exclude future information from signals to ensure backtests are realistic and research-grade.',
        )
        render_research_section(
            'Survivorship Bias',
            'Evaluate the same strategy across a small sample of current names.',
            'Comparing surviving assets sidesteps the poor performance of delisted or failed names.',
            'The sample results vary significantly, underscoring that asset selection can distort conclusions.',
            'Survivorship bias exaggerates robustness when only winning or surviving names are included.',
        )
        render_research_section(
            'Cost and Slippage',
            'Model explicit trading friction and execution slippage.',
            'Transaction costs and slippage are applied to each discrete change in exposure.',
            'Cost adjustments reduce net return and highlight realistic performance expectations.',
            'Including friction is essential for credible, production-ready research.',
        )


if __name__ == '__main__':
    main()
