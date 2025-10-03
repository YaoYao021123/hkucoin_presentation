import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator
import matplotlib.patheffects as pe

# -------- Inputs --------
GLD_CSV = 'GLD_daily_20years.csv'
SPY_CSV = 'SPY_daily_20years.csv'
SVG_OUT = 'gld_spy_20y_monthly_absprice_linear.svg'
PNG_OUT = 'gld_spy_20y_monthly_absprice_linear.png'

# -------- Colors --------
COLOR_GLD = '#F59E0B'
COLOR_SPY = '#6559F9'
TICK_COLOR  = '#CBD5E1'
GRID_COLOR  = '#94A3B8'
FRAME_COLOR = '#64748B'

def pick_price_column(df):
    name_map = {c.lower().replace('_','').replace(' ', ''): c for c in df.columns}
    for key in ('adjclose', 'close'):
        if key in name_map:
            col = name_map[key]
            return df[['Date', col]].rename(columns={col: 'Close'})
    raise ValueError("No 'Close' or 'Adj Close' column found in CSV.")

def clean_to_numeric(s):
    return pd.to_numeric(s.astype(str).str.replace(r'[^0-9.\-]', '', regex=True), errors='coerce')

# 1) Load & clean
gld_raw = pd.read_csv(GLD_CSV, parse_dates=['Date']).sort_values('Date')
spy_raw = pd.read_csv(SPY_CSV, parse_dates=['Date']).sort_values('Date')
gld = pick_price_column(gld_raw); spy = pick_price_column(spy_raw)
gld['Close'] = clean_to_numeric(gld['Close']); spy['Close'] = clean_to_numeric(spy['Close'])
gld = gld.set_index('Date'); spy = spy.set_index('Date')

# 2) 月末重采样（'ME'）
gld_m = gld.resample('ME').last().rename(columns={'Close': 'GLD'})
spy_m = spy.resample('ME').last().rename(columns={'Close': 'SPY'})

# 3) 对齐
df = gld_m.join(spy_m, how='inner').dropna().astype(float)

# 4) Plot（线性、单 y 轴 = 真实比例）
fig, ax = plt.subplots(figsize=(18, 6), facecolor='none')
ax.set_facecolor('none')

ax.plot(df.index, df['GLD'], color=COLOR_GLD, linewidth=2.6, label='GLD')
ax.plot(df.index, df['SPY'], color=COLOR_SPY, linewidth=2.6, label='SPY')

# 轴样式
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(axis='x', colors=TICK_COLOR, labelsize=12, pad=6)
ax.tick_params(axis='y', colors=TICK_COLOR, labelsize=12, pad=6)

# ✅ 线性比例（真实比例）
ax.yaxis.set_major_locator(MaxNLocator(nbins=8, prune='both'))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'${v:,.0f}'))
ax.set_ylabel('Price (USD)', color=TICK_COLOR, fontsize=13)

# 让范围更自然（略留 5% 头尾空间）
ymin = np.floor(min(df.min()) * 0.95 / 10) * 10
ymax = np.ceil(max(df.max()) * 1.05 / 10) * 10
ax.set_ylim(ymin, ymax)

# 网格、边框
ax.grid(axis='y', color=GRID_COLOR, alpha=0.18, linewidth=0.7)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
for side in ('left','bottom'):
    ax.spines[side].set_color(FRAME_COLOR)
    ax.spines[side].set_linewidth(1.2)

ax.set_xlabel('Year', color=TICK_COLOR, fontsize=13)
ax.margins(x=0.01)

# 端点直标（显示真实价格）
def end_label(ax, x, y, text, color):
    t = ax.text(x, y, text, fontsize=13, color=color, va='center', ha='left',
                fontweight=600, clip_on=False)
    t.set_path_effects([pe.withStroke(linewidth=3.5, foreground='white', alpha=0.9)])

last_x = df.index[-1]
end_label(ax, last_x + pd.offsets.Day(5), df['GLD'].iloc[-1], f'GLD  ${df['GLD'].iloc[-1]:,.2f}', COLOR_GLD)
end_label(ax, last_x + pd.offsets.Day(5), df['SPY'].iloc[-1], f'SPY  ${df['SPY'].iloc[-1]:,.2f}', COLOR_SPY)

# 去图例（端点直标）
leg = ax.legend()
if leg: leg.remove()

fig.tight_layout()

# 5) Save
for fpath in (SVG_OUT, PNG_OUT):
    fig.savefig(fpath, dpi=300, transparent=True, bbox_inches='tight')

print('Saved:')
print('-', SVG_OUT)
print('-', PNG_OUT)
print('Monthly points:', len(df))
print('Range:', df.index[0].date(), 'to', df.index[-1].date())
