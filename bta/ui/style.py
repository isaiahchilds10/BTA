from __future__ import annotations
import streamlit as st

CSS = '''
<style>
:root {--bta-red:#f23851;--bta-bg:#090b10;--bta-card:#141820;--bta-border:#2b2f39}
.stApp {background: radial-gradient(ellipse 900px 340px at 65% -100px,#261017 0%,transparent 70%), #090b10;}
[data-testid="stSidebar"] {background:#0d0f15; border-right:1px solid #242734}
[data-testid="stHeader"]{background:transparent}
.block-container {padding-top:1.2rem;max-width:1280px}
section[data-testid="stSidebar"] .stImage {max-width:170px;margin:0 auto}
h1,h2,h3 {letter-spacing:-.035em}
h1{font-size:2.35rem!important;font-weight:900!important}
h2{font-size:1.48rem!important;font-weight:820!important}
.bta-eyebrow {font-size:.72rem;font-weight:800;letter-spacing:.19em;color:#f23851;margin:0 0 .35rem}
.bta-sub {font-size:1rem;color:#aeb4c0;margin:.3rem 0 1rem}
.bta-hero {background:linear-gradient(115deg,#21151d,#12151d 57%,#15191f);border:1px solid #3c2832;border-radius:22px;padding:24px 27px;margin:5px 0 21px;}
.bta-hero strong{font-size:1.7rem;font-weight:900;letter-spacing:-.035em}
.bta-chip{border-radius:99px;padding:.25rem .65rem;font-size:.72rem;font-weight:800;background:#272d3b;color:#e9ecf3;border:1px solid #39404f;display:inline-block}
.bta-chip.red{color:#ff8696;background:#341722;border-color:#693341}
.bta-kpi {background:#141820;border:1px solid #292d37;padding:14px 16px;border-radius:16px;}
.bta-kpi b{font-size:1.7rem;color:white;display:block}
.bta-kpi span{font-size:.78rem;color:#9fa6b3}
.bta-card {border:1px solid #272d38;border-radius:16px;background:#141820;padding:15px 18px;margin-bottom:10px}
.bta-muted{color:#a5abb7;font-size:.85rem}
.bta-small{font-size:.76rem;color:#8c95a5}
.bta-red{color:#ff6478}
div.stButton > button[kind="primary"]{background:linear-gradient(120deg,#ed263f,#b81b34)!important;border:0!important;color:white!important;font-weight:750;border-radius:10px}
[data-testid="stExpander"]{background:#12161e;border:1px solid #292e39;border-radius:12px;margin-bottom:8px}
[data-testid="stMetric"]{background:#171b24;padding:12px;border:1px solid #303440;border-radius:12px}
[data-testid="stMetricLabel"]{color:#aab1c0}
footer {visibility:hidden}
@media(max-width:650px){.block-container{padding-left:.7rem;padding-right:.7rem;padding-top:.6rem}
h1{font-size:1.75rem!important}.bta-hero{padding:16px}.bta-hero strong{font-size:1.24rem} }
</style>
'''

def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
# Floating assistant: position the Streamlit-native popover container; no custom JS or invented chat state.
CSS += '''
<style>
.st-key-bta_float_button {position:fixed!important;right:20px;bottom:22px;z-index:9998!important;max-width:210px!important}
.st-key-bta_float_button button {border-radius:999px!important;background:linear-gradient(120deg,#ea2b44,#a61930)!important;color:#fff!important;border:1px solid #ef5368!important;box-shadow:0 10px 35px #0009;font-weight:800!important}
@media(max-width:680px){.st-key-bta_float_button{bottom:78px!important;right:12px!important;max-width:145px!important}.st-key-bta_float_button button{font-size:.75rem}}
</style>
'''

CSS += """
<style>
@media(max-width:680px){
  .block-container {padding-bottom:130px!important}
  .st-key-bta_primary_nav{position:fixed!important;bottom:0!important;left:0!important;right:0!important;z-index:9996!important;background:#0d0f16!important;border-top:1px solid #35303b;padding:6px 8px 14px!important;box-shadow:0 -12px 32px #0009;overflow-x:auto!important}
  .st-key-bta_primary_nav [data-testid="stSegmentedControl"]{display:flex!important;min-width:460px!important}
}
</style>
"""

# Polished compact top navigation. Minimal market hierarchy and original logo.
CSS += '''
<style>
.st-key-bta_brand_bar {padding:0 0 .4rem 0;border-bottom:1px solid #2f313b;margin-bottom:8px}
.st-key-bta_brand_bar .stImage img {object-fit:contain;max-height:79px}
.bta-brand-name{font-size:1.65rem;font-weight:950;letter-spacing:-.075em;color:#fafbfe;line-height:1.0}
.bta-brand-name span{color:#fa3852}
.bta-brand-tag{font-size:.61rem;letter-spacing:.175em;font-weight:800;color:#8d97a8;margin-top:.35rem}
.st-key-bta_primary_nav {margin:5px 0 14px}
.st-key-bta_primary_nav [data-testid="stSegmentedControl"] {padding:4px;background:#111720;border:1px solid #292f3a;border-radius:15px}
.st-key-bta_primary_nav button {font-weight:800;letter-spacing:.012em}
.st-key-bta_primary_nav button[aria-checked="true"] {background:#bd2039!important;color:white!important}
.bta-count{font-size:.67rem;font-weight:900;color:#b4c0cf;background:#222c38;border-radius:999px;padding:2px 8px;vertical-align:middle}
[data-testid="stVerticalBlockBorderWrapper"]:has(.stButton) {border-color:#292f3a!important}
[data-testid="stPopover"] button {border-radius:12px}
@media(max-width:680px){
  .st-key-bta_brand_bar .stImage img {max-width:57px!important;max-height:57px!important}
  .bta-brand-name{font-size:1.25rem}
  .bta-brand-tag{font-size:.48rem}
  .st-key-bta_primary_nav{margin:0}
  .st-key-bta_primary_nav button{font-size:.76rem;padding:.35rem .4rem}
}
</style>
'''

# iPhone-first refinement: five actual destinations remain visible without
# horizontal scrolling; account for iOS Safari safe-area and home indicator.
CSS += '''
<style>
@media(max-width:680px){
  .block-container{padding-left:11px!important;padding-right:11px!important;
                   padding-bottom:calc(132px + env(safe-area-inset-bottom,0px))!important}
  .st-key-bta_primary_nav{box-sizing:border-box!important;max-width:100vw!important;
      overflow:hidden!important;bottom:0!important;
      padding:5px 5px calc(9px + env(safe-area-inset-bottom,0px))!important}
  .st-key-bta_primary_nav [data-testid="stSegmentedControl"]{
      box-sizing:border-box!important;min-width:0!important;width:100%!important;
      display:flex!important;flex-wrap:nowrap!important;gap:1px!important;
      padding:2px!important;border-radius:12px!important;overflow:hidden!important}
  .st-key-bta_primary_nav [data-testid="stSegmentedControl"] button{
      min-width:0!important;max-width:20%!important;flex:1 1 20%!important;
      font-size:clamp(.59rem,2.4vw,.76rem)!important;line-height:1.15!important;
      white-space:normal!important;overflow-wrap:anywhere!important;
      padding:9px 1px!important;min-height:47px!important}
  .st-key-bta_float_button{
      right:12px!important;bottom:calc(78px + env(safe-area-inset-bottom,0px))!important;
      max-width:140px!important}
  .st-key-bta_float_button button{min-height:44px!important}
  .st-key-bta_brand_bar .stImage img{object-fit:contain!important}
  .bta-hero{border-radius:15px!important;padding:17px 15px!important}
  .bta-card,.bta-kpi{border-radius:12px!important;padding:11px!important}
  /* Metric blocks stack in two columns on narrow screens rather than cramming four. */
  [data-testid="stHorizontalBlock"]:has(.bta-kpi){flex-wrap:wrap!important;gap:9px!important}
  [data-testid="stHorizontalBlock"]:has(.bta-kpi)>[data-testid="stColumn"]{
      flex:1 1 calc(50% - 9px)!important;min-width:calc(50% - 9px)!important}
  .stSelectbox div[data-baseweb="select"],.stTextInput input{min-height:43px}
}
@media(max-width:380px){
  .st-key-bta_primary_nav [data-testid="stSegmentedControl"] button{font-size:.56rem!important}
}
@media(prefers-reduced-motion:reduce){
  *,*:before,*:after{transition:none!important;animation:none!important}
}
</style>
'''

CSS += '''
<style>
.st-key-bta_brand_bar .stButton>button{border:1px solid #66303b!important;background:#26151c!important;color:#ffbbc4!important;border-radius:13px!important;font-weight:800!important;font-size:.84rem!important;min-height:43px!important}
.st-key-bta_brand_bar .stButton>button:hover{border-color:#ec4a65!important;background:#3c1925!important}
@media(max-width:680px){.st-key-bta_brand_bar .stButton>button{font-size:.68rem!important;padding:5px 3px!important;min-height:39px!important}}
</style>
'''
