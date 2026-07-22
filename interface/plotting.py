import plotly.graph_objects as go
from quench_config import STYLES, LINE_STYLES, MARKERS


def plot_style(signal_name, x, y):
    """This function is responsible for plotting using markers, dash, line ...etc"""
    style = STYLES.get(signal_name, {})
    color = style.get("color")
    dash = LINE_STYLES.get(style.get("linestyle", "-"), "solid")
    width = style.get("linewidth", 2)
    opacity = style.get("alpha", 1.0)
    marker_symbol = MARKERS.get(style.get("marker"))
    markersize = style.get("markersize", 6)

    traces = []
    if marker_symbol:
        traces.append(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=signal_name,
                legendgroup=signal_name,
                showlegend=False,
                opacity=opacity,
                line=dict(color=color, dash=dash, width=width),
            )
        )
        markevery = max(style.get("markevery", 1), 1)
        traces.append(
            go.Scatter(
                x=x[::markevery],
                y=y[::markevery],
                mode="markers",
                name=signal_name,
                legendgroup=signal_name,
                showlegend=False,
                opacity=opacity,
                marker=dict(symbol=marker_symbol, size=markersize, color=color,
                            line=dict(width=1, color=color)),
            )
        )
        traces.append(
            go.Scatter(
                x=[None], y=[None],
                mode="lines+markers",
                name=signal_name,
                legendgroup=signal_name,
                showlegend=True,
                line=dict(color=color, dash=dash, width=width),
                marker=dict(symbol=marker_symbol, size=markersize, color=color,
                            line=dict(width=1, color=color)),
            )
        )
    else:
        traces.append(
            go.Scatter(
                x=x, y=y,
                mode="lines",
                name=signal_name,
                legendgroup=signal_name,
                showlegend=True,
                opacity=opacity,
                line=dict(color=color, dash=dash, width=width),
            )
        )

    return traces


def build_figure(signal_data, title):
    """Build the full figure from the signals data."""
    fig = go.Figure()
    for signal_name, (x, y) in signal_data.items():
        for trace in plot_style(signal_name, x, y):
            fig.add_trace(trace)

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        template="plotly_white",
        width=700,
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        dragmode="select",
        uirevision=title,
    )
    return fig


def extract_box_range(box_item):
    """Pull an (x_range, y_range) pair out of a selected part of the event"""
    if "x0" in box_item and "x1" in box_item:
        return sorted([box_item["x0"], box_item["x1"]]), sorted([box_item["y0"], box_item["y1"]])
    if "range" in box_item:
        r = box_item["range"]
        return sorted(r["x"]), sorted(r["y"])
    if "x" in box_item and "y" in box_item:
        return sorted(box_item["x"]), sorted(box_item["y"])
    return None, None
    


