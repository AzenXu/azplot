import datetime
from typing import List
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid, Tab
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from . import utils

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 50)  # 最多显示数据的行数
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)  # 这两行代码是让print输出的内容对齐


class StockChartModel:
    # 包含着OCLH的二维数组
    stock_df: pd.DataFrame
    k_line_OCLH_data: List[List[float]]
    dates: List[datetime.datetime]
    amount: List[float]
    stock_name: str
    returns: List[float]  # 涨跌幅
    start_date: str
    end_date: str
    __up_limits: List = None
    __buy_days: List
    __sell_days: List

    def __init__(self, stock_df, start_date: str, end_date: str, buy_days: List[pd.Timestamp] = None,
                 sell_days: List[pd.Timestamp] = None):
        """
        展示基础K线、成交额、涨跌幅
        :param stock_df:
        :param start_date: 如：2022/10/11
        :param end_date: 如：2023/02/07
        """
        self.stock_df = stock_df
        self.stock_df['涨跌幅'] = (stock_df['收盘价'] / stock_df['前收盘价'] - 1).apply(
            lambda x: float(Decimal(x * 10000).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 100))

        self.k_line_OCLH_data = stock_df[['开盘价', '收盘价', '最低价', '最高价']].values.tolist()
        self.dates = stock_df['交易日期'].dt.strftime('%Y/%m/%d').values.tolist() \
            if is_datetime(stock_df['交易日期']) \
            else stock_df['交易日期'].values.tolist()
        self.amount = stock_df['成交额'].values.tolist()
        self.stock_name = stock_df.iloc[-1]['股票名称']
        self.code = stock_df.iloc[-1]['股票代码']
        self.returns = self.stock_df['涨跌幅'].tolist()
        self.start_date = start_date
        self.end_date = end_date

        # 买/卖点信息
        self.__buy_days = buy_days
        self.__sell_days = sell_days

    def ma(self, day_count):
        return self.stock_df['收盘价'].rolling(day_count).mean().to_list()

    def up_limits(self):
        # 文档
        if self.__up_limits is None:
            up_limit_df = self.stock_df[(self.stock_df.涨跌幅 > 9.89) & (self.stock_df.最高价 == self.stock_df.收盘价)]
            up_limit_df = up_limit_df[['交易日期', '最高价']].assign(
                交易日期=up_limit_df.交易日期.dt.strftime('%Y/%m/%d')).assign(
                最高价=up_limit_df.最高价 * 1.02)
            coords = [row.tolist() for row in up_limit_df.values]
            self.__up_limits = list(map(lambda x: opts.MarkPointItem(name='板', coord=x, value='板',
                                                                     itemstyle_opts=opts.ItemStyleOpts(
                                                                         color='#66ccff')), coords))
        return self.__up_limits

    def buy_data(self):
        if self.__buy_days is None:
            return []
        # 1. 基于buy_days去stock_df里面找对应数据
        buy_df = self.stock_df[self.stock_df.交易日期.isin(self.__buy_days)]
        # 2. 处理方式类似up_limits
        buy_df = buy_df[['交易日期', '最低价']].assign(交易日期=buy_df.交易日期.dt.strftime('%Y/%m/%d')).assign(
            最低价=buy_df.最低价 * 0.98)
        coords = [row.tolist() for row in buy_df.values]
        return list(
            map(lambda x: opts.MarkPointItem(name='买', coord=x, value='买', symbol='arrow', symbol_size=[20, 25],
                                             itemstyle_opts=opts.ItemStyleOpts(
                                                 color='#dc143c')), coords))

    def sell_data(self):
        if self.__sell_days is None:
            return []
        # 1. 基于buy_days去stock_df里面找对应数据
        sell_df = self.stock_df[self.stock_df.交易日期.isin(self.__sell_days)]
        # 2. 处理方式类似up_limits
        sell_df = sell_df[['交易日期', '最低价']].assign(交易日期=sell_df.交易日期.dt.strftime('%Y/%m/%d')).assign(
            最低价=sell_df.最低价 * 0.98)
        coords = [row.tolist() for row in sell_df.values]
        return list(
            map(lambda x: opts.MarkPointItem(name='卖', coord=x, value='卖', symbol='arrow', symbol_size=[20, 25],
                                             itemstyle_opts=opts.ItemStyleOpts(
                                                 color='#228b22')), coords))


class StockChartView(Grid):

    def __init__(self, model: StockChartModel):
        kline = (
            Kline()
            .add_xaxis(xaxis_data=model.dates)
            .add_yaxis(
                series_name=model.stock_name,
                y_axis=model.k_line_OCLH_data,
                itemstyle_opts=opts.ItemStyleOpts(color="#ec0000", color0="#00da3c"),  # # 图元样式配置项，
            )
            # 标记点
            .set_series_opts(
                # 文档：https://pyecharts.org/#/zh-cn/series_options?id=markpointitem%ef%bc%9a%e6%a0%87%e8%ae%b0%e7%82%b9%e6%95%b0%e6%8d%ae%e9%a1%b9
                markpoint_opts=opts.MarkPointOpts(
                    data=model.up_limits() + model.buy_data() + model.sell_data()
                ))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=model.stock_name, subtitle=model.code, pos_left="center"),
                # 设置title    pos_left="120"
                legend_opts=opts.LegendOpts(  # legend_opts图例配置项
                    is_show=False, pos_bottom=10, pos_left="center"
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False,
                        type_="inside",  # 组件类型，可选 "slider", "inside"
                        xaxis_index=[0, 1, 2],
                        range_start=None,  # 数据窗口范围的起始百分比，可以设成80
                        range_end=None,
                        start_value=model.start_date,
                        end_value=model.end_date
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0, 1, 2],  # 如果是 number 表示控制一个轴，如果是 Array 表示控制多个轴。
                        type_="slider",
                        pos_top="70%",
                        range_start=None,
                        range_end=None,
                        start_value='2022/10/11',
                        end_value='2023/02/07'
                    ),
                ],
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    ),
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.8)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000"),
                ),
                visualmap_opts=opts.VisualMapOpts(
                    is_show=False,
                    dimension=2,
                    series_index=(5, 6, 7),
                    # series_index=None, # 取所有列的数据, 这里改成none或all都是副图有红绿柱，主图没有。
                    is_piecewise=True,
                    pieces=[
                        {"value": 1, "color": "#00da3c"},
                        {"value": -1, "color": "#ec0000"},
                    ],
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
                brush_opts=opts.BrushOpts(
                    x_axis_index="all",  # 指定哪些 xAxisIndex 可以被刷选。可以设置 brush 是全局的还是属于坐标系的。
                    brush_link="all",
                    out_of_brush={"colorAlpha": 0.1},  # 定义在选中范围外的视觉元素。最终参数以字典的形式进行配置
                    brush_type="lineX",  # 默认的刷子类型。默认值为 rect。# "lineX"：横向选择。
                ),
            )
        )

        ma_line = (
            Line()
            .add_xaxis(xaxis_data=model.dates)
            .add_yaxis(
                series_name="MA5",
                y_axis=model.ma(5),
                symbol_size=0,
                is_smooth=True,  # 曲线平滑
                is_hover_animation=False,  # 是否开启 hover 在拐点标志上的提示动画效果。
                linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),  # 线样式配置项
                label_opts=opts.LabelOpts(is_show=False),  # 标签配置项
            )
            .add_yaxis(
                series_name="MA150",
                y_axis=model.ma(150),
                symbol_size=0,
                is_smooth=True,
                is_hover_animation=False,
                linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),
                label_opts=opts.LabelOpts(is_show=False),
            )
        )

        amount_bar = (
            Bar()
            .add_xaxis(xaxis_data=model.dates)
            .add_yaxis(
                series_name="成交额",
                y_axis=model.amount,
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
                          page_title=model.stock_name,  # 网页标题，控制网页卡的显示内容
                          animation_opts=opts.AnimationOpts(animation=False),
                      ))
        self.add(kline.overlap(ma_line), grid_opts=opts.GridOpts(pos_left='10%', pos_right='8%', height='40%'))
        self.add(amount_bar, grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="48%", height="12%"))
        self.add(returns_bar, grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="60%", height="12%"))


class StockChartController:
    stock_data_dir = ""

    def __init__(self, stock_data_dir: str):
        self.stock_data_dir = stock_data_dir

    def _get_chart_model(self, code, buy_days: [pd.Timestamp] = None, sell_days: [pd.Timestamp] = None,
                         window_start='2022/10/11', window_end='2023/02/07', stick_count=None):
        """
        有stick_count就用，没有就用window_start和window_end
        :param code:
        :param buy_days:
        :param sell_days:
        :param window_start:
        :param window_end:
        :param stick_count:
        :return:
        """
        stock_data = pd.read_csv(f'{self.stock_data_dir}/{code}.csv', encoding='gbk', skiprows=1,
                                 parse_dates=['交易日期'])
        # 停牌日K线不显示
        stock_data.dropna(subset=['成交额'], inplace=True, axis=0)
        stock_data.sort_values('交易日期', inplace=True)
        stock_data.reset_index(drop=True, inplace=True)
        if buy_days is not None and len(buy_days) > 0 and stick_count is not None:
            buy_day = buy_days[0]
            middle_index = stock_data[stock_data.交易日期 == buy_day].index.astype(int)[0]
            left_index = int(0 if middle_index < stick_count * 0.5 else middle_index - stick_count * 0.5)
            right_index = int(stock_data.index[-1] if middle_index + stick_count * 0.5 > stock_data.index[
                -1] else middle_index + stick_count * 0.5)
            window_start = stock_data.iloc[left_index].交易日期.strftime('%Y/%m/%d')
            window_end = stock_data.iloc[right_index].交易日期.strftime('%Y/%m/%d')

        model = StockChartModel(stock_df=stock_data, start_date=window_start, end_date=window_end,
                                buy_days=buy_days, sell_days=sell_days)
        return model

    def draw_stock(self, code, buy_days: [pd.Timestamp] = None, sell_days: [pd.Timestamp] = None,
                   window_start='2022/10/11', window_end='2023/02/07'):
        """
        :param code:
        :param window_start: 如：2022/10/11
        :param window_end: 如：2023/02/07
        :return:
        """
        import webbrowser
        model = self._get_chart_model(code, buy_days, sell_days, window_start, window_end)
        chart_result = StockChartView(model=model).render()

        webbrowser.open_new(chart_result)
        return chart_result

    def draw_stocks(self, stocks_df: pd.DataFrame, page_title: str = '股票走势图'):
        """
        :param page_title: 图表名
        :param stocks_df: 必填字段 - 股票代码、股票名称；选填字段 - 交易日期（pd.Timestamp）
        :return:
        """
        utils.df_check(stocks_df, ['股票代码', '股票名称'])
        stocks_df = stocks_df.copy()
        stocks_df['股票代码'] = stocks_df.股票代码.str.strip()
        import webbrowser
        tab = Tab(page_title=page_title)
        for i in stocks_df.index:
            one_stock = stocks_df[i:i + 1]
            name = one_stock.股票名称.iloc[0]
            code = one_stock.股票代码.iloc[0]
            buy_days = []
            buy_day_str = ''
            if '交易日期' in one_stock.columns:
                buy_days = [one_stock.交易日期.iloc[0]]
                buy_day_str = one_stock.交易日期.iloc[0].strftime('%Y-%m-%d')

            tab.add(StockChartView(self._get_chart_model(code=code, buy_days=buy_days, stick_count=100)),
                    tab_name=buy_day_str + name)

        webbrowser.open_new(tab.render(path=f"{page_title}.html"))
        print(tab)


def draw_stock(code, stock_data_dir=r'D:\Work\Code\azen-quant\data\xbx_stock_data\data\stock-trading-data-pro', buy_days: [pd.Timestamp] = None, sell_days: [pd.Timestamp] = None,
               window_start='2022/10/11', window_end='2023/02/07'):
    StockChartController(stock_data_dir=stock_data_dir).draw_stock(code=code, buy_days=buy_days, sell_days=sell_days,
                                                                   window_start=window_start, window_end=window_end)


if __name__ == '__main__':
    # StockChartController(stock_data_dir=r'D:\Work\Code\azen-quant\data\xbx_stock_data\data\stock-trading-data-pro') \
    #     .draw_stock(code='sh601360', window_start='2022/10/11', window_end='2023/02/07',
    #                 buy_days=[pd.Timestamp('2023-02-07'), pd.Timestamp('2023-02-06')],
    #                 sell_days=[pd.Timestamp('2023-02-09'), pd.Timestamp('2023-02-10')])

    # StockChartController(stock_data_dir=r'D:\Work\Code\azen-quant\data\xbx_stock_data\data\stock-trading-data-pro') \
    #     .draw_stocks(stocks_df=pd.DataFrame(
    #         {'股票代码': ['sh601360'], '股票名称': ['三六零'], '交易日期': [pd.Timestamp('2023-04-11')]}))

    StockChartController(stock_data_dir=r'D:\Work\Code\azen-quant\data\xbx_stock_data\data\stock-trading-data-pro') \
        .draw_stock(code='sh601360', window_start='2022/10/11', window_end='2023/02/07')
