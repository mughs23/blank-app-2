import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Steel Connection Checker")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Connection Selection")
connection = st.sidebar.selectbox(
    "Select Connection Type",
    [
        "Extended fin plate - beam-to-beam (similar depth)",
        "Extended fin plate - beam-to-beam (different depth)",
        "Beam-to-column",
        "End plate"
    ]
)

st.sidebar.header("Loads")
V_ed = st.sidebar.number_input("Applied shear force V_ed (kN)", min_value=0.0, value=400.0)

st.sidebar.header("Bolt Inputs")
bolt_d = st.sidebar.number_input("Bolt diameter (mm)", min_value=12, step=1, value=20)
n_bolts = st.sidebar.number_input("Number of bolts per line", min_value=2, step=1, value=5)
fub = st.sidebar.number_input("Bolt ultimate strength fub (MPa)", min_value=0.0, value=800.0)

st.sidebar.header("Geometry Inputs")
e1 = st.sidebar.number_input("End distance e1 (mm)", min_value=10.0, value=70.0)
e2 = st.sidebar.number_input("Edge distance e2 (mm)", min_value=10.0, value=50.0)
p1 = st.sidebar.number_input("Pitch p1 (mm)", min_value=20.0, value=60.0)
p2 = st.sidebar.number_input("Gauge p2 (mm)", min_value=40.0, value=120.0)
tp = st.sidebar.number_input("Plate thickness tp (mm)", min_value=4.0, value=12.0)
fu = st.sidebar.number_input("Plate ultimate strength fu (MPa)", min_value=0.0, value=490.0)

st.sidebar.header("Member Geometry")
beam_depth = st.sidebar.number_input("Beam depth (mm)", min_value=200.0, value=500.0)
beam_length = st.sidebar.number_input("Visible beam length each side (mm)", min_value=250.0, value=500.0)
beam_gap = st.sidebar.number_input("Gap between beams / support zone (mm)", min_value=80.0, value=140.0)
support_width = st.sidebar.number_input("Support web width (mm)", min_value=20.0, value=40.0)

gamma_M2 = 1.25

# =========================
# CALCULATIONS
# =========================
bolt_area_map = {
    12: 84.3,
    16: 157.0,
    20: 245.0,
    22: 303.0,
    24: 353.0,
    27: 459.0,
    30: 561.0,
}

A_s = bolt_area_map.get(int(bolt_d), 245.0)
d0 = bolt_d + 2.0

Fv_Rd = (0.6 * fub * A_s) / gamma_M2 / 1000.0
k1 = min((2.8 * e2 / d0 - 1.7), (1.4 * p2 / d0 - 1.7), 2.5)
alpha_b = min((e1 / (3.0 * d0)), (p1 / (3.0 * d0) - 0.25), (fub / fu), 1.0)
Fb_Rd = (k1 * alpha_b * fu * bolt_d * tp) / gamma_M2 / 1000.0
V_rd = min(Fv_Rd * n_bolts, Fb_Rd * n_bolts)
utilization = V_ed / V_rd if V_rd > 0 else 0.0
governing_mode = "Bolt shear governs" if Fv_Rd < Fb_Rd else "Bearing governs"

# =========================
# PLOTLY HELPERS
# =========================
def rect_shape(x0, y0, x1, y1, line_width=2):
    return dict(
        type="rect",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line=dict(width=line_width, color="black"),
        fillcolor="rgba(0,0,0,0)"
    )

def circle_shape(x, y, r, line_width=1.5):
    return dict(
        type="circle",
        x0=x-r, y0=y-r, x1=x+r, y1=y+r,
        line=dict(width=line_width, color="black"),
        fillcolor="rgba(0,0,0,0)"
    )

def add_dimension(fig, x0, y0, x1, y1, label, text_x, text_y):
    fig.add_annotation(
        x=x1, y=y1, ax=x0, ay=y0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.2
    )
    fig.add_annotation(
        x=x0, y=y0, ax=x1, ay=y1,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.2
    )
    fig.add_annotation(
        x=text_x, y=text_y, text=label,
        showarrow=False, font=dict(size=12)
    )

def add_force_arrow(fig, x, y_top, y_bot, label):
    fig.add_annotation(
        x=x, y=y_bot, ax=x, ay=y_top,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2
    )
    fig.add_annotation(
        x=x + 25, y=y_top + 10, text=label,
        showarrow=False, font=dict(size=12)
    )

def add_moment_label(fig, x, y, label):
    fig.add_annotation(x=x, y=y, text=label, showarrow=False, font=dict(size=12))

def build_beam_to_beam_fin_figure(conn_label, bolt_d, n_bolts, e1, e2, p1, p2, tp, V_ed,
                                  beam_depth, beam_length, beam_gap, support_width):
    fig = go.Figure()

    # Geometry derived from inputs
    plate_height = 2 * e1 + (n_bolts - 1) * p1
    plate_width = max(70.0, 2 * e2 + bolt_d + 20.0)

    left_beam_x0 = 0.0
    left_beam_x1 = beam_length
    support_x0 = beam_length + beam_gap / 2 - support_width / 2
    support_x1 = support_x0 + support_width
    right_beam_x0 = beam_length + beam_gap
    right_beam_x1 = right_beam_x0 + beam_length

    left_beam_y0 = 0.0
    left_beam_y1 = beam_depth

    if "different depth" in conn_label.lower():
        right_beam_y0 = beam_depth * 0.12
        right_beam_y1 = right_beam_y0 + beam_depth * 0.82
    else:
        right_beam_y0 = 0.0
        right_beam_y1 = beam_depth

    plate_y0_left = (left_beam_y0 + left_beam_y1) / 2 - plate_height / 2
    plate_y1_left = plate_y0_left + plate_height

    plate_y0_right = (right_beam_y0 + right_beam_y1) / 2 - plate_height / 2
    plate_y1_right = plate_y0_right + plate_height

    left_plate_x1 = support_x0
    left_plate_x0 = left_plate_x1 - tp

    right_plate_x0 = support_x1
    right_plate_x1 = right_plate_x0 + tp

    # Beams
    fig.add_shape(rect_shape(left_beam_x0, left_beam_y0, left_beam_x1, left_beam_y1))
    fig.add_shape(rect_shape(right_beam_x0, right_beam_y0, right_beam_x1, right_beam_y1))

    # Support web
    fig.add_shape(rect_shape(support_x0, -120, support_x1, beam_depth + 120))

    # Top and bottom cap plates
    cap_w = max(120.0, support_width + 90.0)
    cap_x0 = (support_x0 + support_x1) / 2 - cap_w / 2
    cap_x1 = cap_x0 + cap_w
    fig.add_shape(rect_shape(cap_x0, beam_depth + 20, cap_x1, beam_depth + 50))
    fig.add_shape(rect_shape(cap_x0, -50, cap_x1, -20))

    # Fin plates
    fig.add_shape(rect_shape(left_plate_x0, plate_y0_left, left_plate_x1, plate_y1_left))
    fig.add_shape(rect_shape(right_plate_x0, plate_y0_right, right_plate_x1, plate_y1_right))

    # Bolts
    bolt_r = max(8.0, bolt_d / 2.8)

    left_bolt_x = left_plate_x0 - e2
    right_bolt_x = right_plate_x1 + e2

    left_start_y = plate_y0_left + e1
    right_start_y = plate_y0_right + e1

    left_bolt_x = left_beam_x1 - e2
    right_bolt_x = right_beam_x0 + e2

    for i in range(int(n_bolts)):
        y_left = left_start_y + i * p1
        y_right = right_start_y + i * p1
        fig.add_shape(circle_shape(left_bolt_x, y_left, bolt_r))
        fig.add_shape(circle_shape(right_bolt_x, y_right, bolt_r))

    # Force arrows
    add_force_arrow(fig, (left_beam_x1 + support_x0) / 2, beam_depth + 120, beam_depth + 30, f"V_ed = {V_ed:.0f} kN")
    add_force_arrow(fig, (support_x1 + right_beam_x0) / 2, beam_depth + 120, beam_depth + 30, f"V_ed = {V_ed:.0f} kN")

    # Moment labels
    add_moment_label(fig, beam_length * 0.3, beam_depth * 0.7, "M_ed")
    add_moment_label(fig, right_beam_x0 + beam_length * 0.7, right_beam_y0 + (right_beam_y1 - right_beam_y0) * 0.7, "M_ed")

    # Text labels
    fig.add_annotation(x=beam_length * 0.5, y=beam_depth + 35, text="Left beam", showarrow=False)
    fig.add_annotation(x=right_beam_x0 + beam_length * 0.5, y=right_beam_y1 + 35, text="Right beam", showarrow=False)
    fig.add_annotation(x=(support_x0 + support_x1) / 2, y=-90, text="Support web", showarrow=False)
    fig.add_annotation(x=left_plate_x0 - 20, y=plate_y1_left + 25, text="Fin plate", showarrow=False)
    fig.add_annotation(x=right_plate_x1 + 20, y=plate_y1_right + 25, text="Fin plate", showarrow=False)
    fig.add_annotation(
        x=(left_beam_x1 + right_beam_x0) / 2,
        y=beam_depth + 85,
        text=f"{int(n_bolts)} bolts per line, M{int(bolt_d)}",
        showarrow=False
    )

    # Dimensions that actually update
    add_dimension(
        fig,
        left_plate_x0 - 60, plate_y0_left,
        left_plate_x0 - 60, left_start_y,
        f"e1 = {e1:.0f}",
        left_plate_x0 - 95, (plate_y0_left + left_start_y) / 2
    )

    if n_bolts > 1:
        add_dimension(
            fig,
            left_plate_x0 - 60, left_start_y,
            left_plate_x0 - 60, left_start_y + p1,
            f"p1 = {p1:.0f}",
            left_plate_x0 - 95, left_start_y + p1 / 2
        )

    add_dimension(
        fig,
        left_beam_x1 - e2, plate_y0_left - 35,
        left_beam_x1, plate_y0_left - 35,
        f"e2 = {e2:.0f}",
        left_beam_x1 - e2 / 2, plate_y0_left - 55
    )

    add_dimension(
        fig,
        left_plate_x0, plate_y0_left - 80,
        left_plate_x1, plate_y0_left - 80,
        f"tp = {tp:.0f}",
        (left_plate_x0 + left_plate_x1) / 2, plate_y0_left - 100
    )

    add_dimension(
        fig,
        left_start_y, beam_depth + 70,
        left_start_y + (n_bolts - 1) * p1, beam_depth + 70,
        f"bolt line = {(n_bolts - 1) * p1:.0f}",
        left_start_y + (n_bolts - 1) * p1 / 2, beam_depth + 95
    )

    total_width = right_beam_x1 - left_beam_x0
    total_height_min = min(-130, right_beam_y0 - 130)
    total_height_max = max(beam_depth + 140, right_beam_y1 + 140)

    fig.update_xaxes(
        visible=False,
        range=[-80, total_width + 80],
        scaleanchor="y",
        scaleratio=1
    )
    fig.update_yaxes(
        visible=False,
        range=[total_height_min, total_height_max]
    )

    fig.update_layout(
        height=650,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        dragmode="pan",
    )

    return fig

# =========================
# LAYOUT
# =========================
left, right = st.columns([0.9, 1.6])

with left:
    st.subheader("Inputs Summary")
    st.write(f"Connection: {connection}")
    st.write(f"Applied shear V_ed = {V_ed:.2f} kN")
    st.write(f"Bolt diameter = M{int(bolt_d)}")
    st.write(f"Number of bolts per line = {n_bolts}")
    st.write(f"Bolt area A_s = {A_s:.1f} mm²")
    st.write(f"Hole diameter d0 = {d0:.1f} mm")
    st.write(f"e1 = {e1:.1f} mm")
    st.write(f"e2 = {e2:.1f} mm")
    st.write(f"p1 = {p1:.1f} mm")
    st.write(f"p2 = {p2:.1f} mm")
    st.write(f"tp = {tp:.1f} mm")
    st.write(f"Beam depth = {beam_depth:.1f} mm")
    st.write(f"Beam gap = {beam_gap:.1f} mm")

    st.divider()

    st.subheader("Design Check Result")
    if V_rd >= V_ed:
        st.success(f"PASS — Capacity {V_rd:.2f} kN ≥ Demand {V_ed:.2f} kN")
    else:
        st.error(f"FAIL — Capacity {V_rd:.2f} kN < Demand {V_ed:.2f} kN")

    if utilization < 0.6:
        st.info(f"Utilization = {utilization:.2f} (Efficient)")
    elif utilization < 1.0:
        st.warning(f"Utilization = {utilization:.2f} (Near limit)")
    else:
        st.error(f"Utilization = {utilization:.2f} (Overstressed)")

    st.write(f"Governing mode: {governing_mode}")

    st.divider()

    st.subheader("Calculations")
    st.latex(r"F_{v,Rd} = \frac{0.6 \cdot f_{ub} \cdot A_s}{\gamma_{M2}}")
    st.write(f"Fv,Rd = {Fv_Rd:.2f} kN per bolt")
    st.write(f"k₁ = {k1:.2f}")
    st.write(f"α_b = {alpha_b:.2f}")
    st.write(f"Fb,Rd = {Fb_Rd:.2f} kN per bolt")
    st.write(f"V_rd = {V_rd:.2f} kN")

with right:
    st.subheader("Connection Visualization")

    if "beam-to-beam" in connection.lower():
        fig = build_beam_to_beam_fin_figure(
            connection, bolt_d, n_bolts, e1, e2, p1, p2, tp, V_ed,
            beam_depth, beam_length, beam_gap, support_width
        )
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
        st.caption("This view is zoomable and pans in-browser. Geometry updates with the inputs.")
    else:
        st.info("This upgraded interactive view is currently built for the beam-to-beam fin plate case first.")
