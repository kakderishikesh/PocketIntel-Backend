import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def plot_line_chart(df: pd.DataFrame, x: str, y: str, title: str):
    """
    Create a simple line chart.
    """
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    fig.update_layout(template="plotly_white")
    return fig


def plot_bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    """
    Create a simple vertical bar chart.
    """
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_layout(template="plotly_white")
    return fig


def plot_stacked_bar_chart(df: pd.DataFrame, x: str, y_keys: list, title: str):
    """
    Create a stacked bar chart for sentiment or grouped data.
    `y_keys` should be the list of column names to stack.
    """
    fig = go.Figure()
    for y in y_keys:
        fig.add_trace(go.Bar(name=y.capitalize(), x=df[x], y=df[y]))
    fig.update_layout(barmode='stack', title=title, template="plotly_white")
    return fig


def plot_multi_line_chart(df: pd.DataFrame, x: str, y_keys: list, title: str):
    """
    Multi-line chart from several y-series.
    """
    fig = go.Figure()
    for y in y_keys:
        fig.add_trace(go.Scatter(x=df[x], y=df[y], mode='lines+markers', name=y))
    fig.update_layout(title=title, template="plotly_white")
    return fig
