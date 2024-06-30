from pyecharts.charts import Line
import datetime
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from typing import List

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Grid
from . import utils

def draw_stock_line_chart(df: pd.DataFrame, stock_column_name: str = '股票代码', title: str = '股票价格走势图'):
    """
    绘制股票价格折线图
    :param df: 包含股票价格数据的DataFrame，索引为pd.Timestamp类型，且包含名为'股票代码'的列
    :param stock_column_name: 存储股票代码的列名，默认为'股票代码'
    :param title: 图表标题
    """
    if stock_column_name not in df.columns:
        raise ValueError(f"DataFrame must contain column '{stock_column_name}'")

    # 检查索引是否为Datetime类型
    if not is_datetime(df.index):
        raise TypeError("Index of DataFrame must be of type pd.Timestamp")

    # 创建折线图对象
    stock_line = (
        Line()
        .add_xaxis(xaxis_data=df.index.strftime('%Y-%m-%d'))
        .add_yaxis(
            series_name=stock_column_name,
            y_axis=df[stock_column_name].tolist(),
            symbol_size=4,
            is_symbol_show=True,
            is_smooth=True,
            is_hover_animation=False
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
            yaxis_opts=opts.AxisOpts(split_number=3, is_scale=True)
        )
    )

    # 渲染图表到HTML文件，并在默认浏览器中打开
    chart_result = stock_line.render()
    import webbrowser
    webbrowser.open_new(chart_result)
    return chart_result

# 示例使用
# 假设df是您的DataFrame，并且已经满足上述条件
# draw_stock_line_chart(df, '股票代码')