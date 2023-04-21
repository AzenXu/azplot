import datetime
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from typing import List

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Grid
import azhint


class NetLineModel:
    name: str
    dates: List[datetime.datetime]
    equity_df: pd.DataFrame
    net_values: List[float]
    benchmark: List[float]
    returns: List[float]

    def __init__(self, equity_df: pd.DataFrame, name: str):
        """
        :param equity_df: ['equity_curve'：净值, '涨跌幅', 'benchmark'：基准净值]
        :return:
        """
        azhint.df_check(equity_df, ['equity_curve', '涨跌幅', 'benchmark'])
        self.equity_df = equity_df
        self.dates = equity_df.index.strftime('%Y/%m/%d').values.tolist() \
            if is_datetime(equity_df.index) \
            else equity_df.index.values.tolist()
        self.net_values = equity_df.equity_curve.to_list()
        self.benchmark = equity_df.benchmark.to_list()
        self.returns = equity_df.涨跌幅.to_list()
        self.name = name


class NetLineView(Grid):

    def __init__(self, model: NetLineModel):
        net_line = (
            Line()
            .add_xaxis(xaxis_data=model.dates)
            .add_yaxis(
                series_name="净值",
                y_axis=model.net_values,
                symbol_size=0,
                is_smooth=False,  # 曲线平滑
                is_hover_animation=False,  # 是否开启 hover 在拐点标志上的提示动画效果。
                linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),  # 线样式配置项
                label_opts=opts.LabelOpts(is_show=False),  # 标签配置项
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最大值"),
                        opts.MarkPointItem(type_="min", name="最小值"),
                    ]
                ),
                markline_opts=opts.MarkLineOpts(
                    data=[opts.MarkLineItem(type_="average", name="平均值")]
                ),
            )
            .add_yaxis(
                series_name="基准净值",
                y_axis=model.benchmark,
                symbol_size=0,
                is_smooth=False,
                is_hover_animation=False,
                linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),
                label_opts=opts.LabelOpts(is_show=False)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=model.name, subtitle='策略净值', pos_left="center"),
                legend_opts=opts.LegendOpts(  # legend_opts图例配置项
                    is_show=False, pos_bottom=10, pos_left="center"
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False,
                        type_="inside",  # 组件类型，可选 "slider", "inside"
                        xaxis_index=[0, 1, 2],
                        range_start=0,  # 数据窗口范围的起始百分比，可以设成80
                        range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0, 1, 2],  # 如果是 number 表示控制一个轴，如果是 Array 表示控制多个轴。
                        type_="slider",
                        pos_top="80%",
                        range_start=0,
                        range_end=100
                    ),
                ],
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    ),
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                toolbox_opts=opts.ToolboxOpts(is_show=True),
                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
            )
        )

        returns_bar = (
            Bar()
            .add_xaxis(xaxis_data=model.dates)
            .add_yaxis(
                series_name="涨跌幅",
                y_axis=model.returns,
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,
                    grid_index=1,
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    split_number=20,
                    min_="dataMin",
                    max_="dataMax",
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    is_scale=True,
                    split_number=2,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    axisline_opts=opts.AxisLineOpts(is_show=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )

        # Grid Overlap + Bar
        Grid.__init__(self,
                      init_opts=opts.InitOpts(
                          width="1600px",  # 图表画布宽度，css 长度单位
                          height="800px",
                          page_title=model.name,  # 网页标题，控制网页卡的显示内容
                          animation_opts=opts.AnimationOpts(animation=False),
                      ))
        self.add(net_line, grid_opts=opts.GridOpts(pos_left='10%', pos_right='8%', height='70%'))
        self.add(returns_bar, grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="80%", height="20%"))


class NetLineController:
    def draw(self, equity_df: pd.DataFrame, name: str = '策略净值'):
        import webbrowser
        model = NetLineModel(equity_df=equity_df, name=name)
        chart_result = NetLineView(model=model).render()

        webbrowser.open_new(chart_result)
        return chart_result


def draw_net_value(equity_df: pd.DataFrame, name: str = '策略净值'):
    NetLineController().draw(equity_df=equity_df, name=name)

