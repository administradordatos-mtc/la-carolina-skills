import json, sys
sys.stdout.reconfigure(encoding='utf-8')

els = []

def r(id, x, y, w, h, bg, stroke="#1e1e2e", sw=2, roughness=0, opacity=100, rounded=True):
    return {"id":id,"type":"rectangle","x":x,"y":y,"width":w,"height":h,"angle":0,
            "strokeColor":stroke,"backgroundColor":bg,"fillStyle":"solid","strokeWidth":sw,
            "strokeStyle":"solid","roughness":roughness,"opacity":opacity,
            "roundness":{"type":3} if rounded else None,
            "version":1,"versionNonce":hash(id)%999999,"isDeleted":False,"groupIds":[],
            "boundElements":[],"updated":1,"link":None,"locked":False}

def t(id, x, y, w, h, txt, fs=13, color="#1e1e2e", align="center"):
    return {"id":id,"type":"text","x":x,"y":y,"width":w,"height":h,"angle":0,
            "strokeColor":color,"backgroundColor":"transparent","fillStyle":"solid",
            "strokeWidth":1,"strokeStyle":"solid","roughness":0,"opacity":100,"text":txt,
            "fontSize":fs,"fontFamily":2,"textAlign":align,"verticalAlign":"top",
            "lineHeight":1.25,"version":1,"versionNonce":hash(id)%999999,"isDeleted":False,
            "groupIds":[],"boundElements":[],"updated":1,"link":None,"locked":False,"originalText":txt}

def ln(id, x1, y1, x2, y2, color="#adb5bd", sw=1, dash=False):
    return {"id":id,"type":"line","x":x1,"y":y1,"width":x2-x1,"height":y2-y1,"angle":0,
            "strokeColor":color,"backgroundColor":"transparent","fillStyle":"solid","strokeWidth":sw,
            "strokeStyle":"dashed" if dash else "solid","roughness":0,"opacity":100,
            "points":[[0,0],[x2-x1,y2-y1]],"version":1,"versionNonce":hash(id)%999999,
            "isDeleted":False,"groupIds":[],"boundElements":[],"updated":1,"link":None,"locked":False,
            "startBinding":None,"endBinding":None,"startArrowhead":None,"endArrowhead":None}

P = 14

# TITULO
els += [
    r("ttl_bg", 50, 30, 1100, 68, "#cba6f7"),
    t("ttl_1", 50, 42, 1100, 28, "RRHH La Carolina — Rotacion de Conductores 2025", 22, "#1e1e2e", "center"),
    t("ttl_2", 50, 74, 1100, 18, "Fuente: Procesos de reclutamiento.xlsx  |  Periodo: Enero-Julio 2025  |  154 retiros  |  296 contratados  |  3.525 candidatos", 12, "#4a4569", "center"),
]

# KPIs
kpis = [
    ("#89b4fa", "154",       "Total Retiros",       "Ene-Jul 2025 (7 meses)", "#003080"),
    ("#f9e2af", "22 / mes",  "Promedio Mensual",    "pico: 30 (Abr y Jul)", "#7c5e00"),
    ("#f38ba8", "22%",       "Rotacion Temprana",   "35 conductores en <=30 dias", "#8e0020"),
    ("#a6e3a1", "8.4%",      "Tasa Conversion",     "de 3.525 candidatos -> 296", "#155726"),
]
kw, kg, kx0, ky = 262, 14, 50, 115
for i,(bg,val,lbl,sub,tc) in enumerate(kpis):
    x = kx0 + i*(kw+kg)
    els += [
        r(f"kpi{i}", x, ky, kw, 95, bg),
        t(f"kpiv{i}", x, ky+8, kw, 40, val, 32, tc, "center"),
        t(f"kpil{i}", x, ky+50, kw, 18, lbl, 14, "#1e1e2e", "center"),
        t(f"kpis{i}", x, ky+68, kw, 15, sub, 11, "#6c6f85", "center"),
    ]

# GRAFICO BARRAS
els.append(t("s2_lbl", 50, 228, 700, 16, "RETIROS POR MES  /  Balance mensual Contratados vs Retirados", 11, "#6c6f85", "left"))
els.append(r("chart_bg", 50, 245, 1100, 230, "#f8f8f2", "#dee2e6", 1, 0))

months_data = [
    ('Ene', 18, 46, '+28', '#a6e3a1', '#155726'),
    ('Feb', 18, 19,  '+1', '#f9e2af', '#7c5e00'),
    ('Mar', 19, 26,  '+7', '#a6e3a1', '#155726'),
    ('Abr', 30, 23,  '-7', '#f38ba8', '#8e0020'),
    ('May', 18, 25,  '+7', '#a6e3a1', '#155726'),
    ('Jun', 21, 14,  '-7', '#eba0ac', '#8e0020'),
    ('Jul', 30, 22,  '-8', '#f38ba8', '#8e0020'),
]

BASE = 450; MAX_H = 185; MAX_R = 30
BW = 115; GAP = 21; BX0 = 90
AVG_Y = BASE - int(22/MAX_R * MAX_H)

# linea promedio
els.append(ln("avg_ln", 60, AVG_Y, 1140, AVG_Y, "#fab387", 2, True))
els.append(t("avg_lbl", 1048, AVG_Y-16, 90, 14, "prom 22", 10, "#fab387", "center"))

for i,(mes, ret, con, bal, bg, tc) in enumerate(months_data):
    x = BX0 + i*(BW+GAP)
    h = int(ret/MAX_R * MAX_H)
    bar_top = BASE - h
    els.append(r(f"b{i}", x, bar_top, BW, h, bg, "#1e1e2e", 1, 0, 100, False))
    els.append(t(f"bv{i}", x, bar_top-22, BW, 18, str(ret), 16, tc, "center"))
    els.append(t(f"bm{i}", x, BASE+6, BW, 16, mes, 13, "#1e1e2e", "center"))
    bal_color = "#155726" if bal.startswith('+') else "#8e0020"
    els.append(t(f"bb{i}", x, BASE+24, BW, 14, f"bal {bal}", 10, bal_color, "center"))
    els.append(t(f"bc{i}", x, BASE+38, BW, 13, f"cont {con}", 9, "#4a4569", "center"))

# PANEL 1: EMBUDO
els.append(t("s3a_lbl", 50, 498, 380, 16, "EMBUDO DE SELECCION", 11, "#6c6f85", "left"))
els.append(r("p1_bg", 50, 514, 350, 228, "#e7f5ff", "#74c0fc", 1))

funnel = [
    (300, "#74c0fc", "3.525 candidatos", "100% ingresaron al proceso", "#003080"),
    (240, "#4dabf7", "296 CONTRATADOS",  "Tasa de conversion: 8.4%",  "#003080"),
    (180, "#339af0", "3.087 no contrat.","91.6% cierre de proceso",   "#003080"),
    (120, "#1971c2", "156 REINGRESOS",   "52.7% de contratados",      "#ffffff"),
]
fy0 = 528; fh = 46; fg = 6
fcx = 225
for j,(fw,bg,lbl,sub,tc) in enumerate(funnel):
    fx = fcx - fw//2
    fy = fy0 + j*(fh+fg)
    els.append(r(f"fn{j}", fx, fy, fw, fh, bg, "#1e1e2e", 1, 0, 100, True))
    els.append(t(f"fnl{j}", fx, fy+6, fw, 18, lbl, 13, tc, "center"))
    els.append(t(f"fns{j}", fx, fy+25, fw, 14, sub, 10, tc, "center"))

# PANEL 2: CANALES
els.append(t("s3b_lbl", 430, 498, 380, 16, "CANAL DE POSTULACION (n=3.525)", 11, "#6c6f85", "left"))
els.append(r("p2_bg", 430, 514, 370, 228, "#fff9db", "#ffd43b", 1))

canales = [
    ("WhatsApp",      2897, 82.1, "#fab387"),
    ("Computrabajo",   313,  8.9, "#74c0fc"),
    ("Referido",       199,  5.6, "#a9e34b"),
    ("ManyChat",        68,  1.9, "#e599f7"),
    ("Otros",           48,  1.4, "#adb5bd"),
]
MAX_CW = 270; cy0 = 530; ch = 33; cg = 7; cx_lbl = 445
for j,(name,n,pct,bg) in enumerate(canales):
    bw = max(int(pct/82.1 * MAX_CW), 8)
    cy = cy0 + j*(ch+cg)
    els.append(r(f"ch{j}", cx_lbl, cy, bw, ch, bg, "#1e1e2e", 1, 0, 100, False))
    els.append(t(f"chl{j}", cx_lbl+5, cy+8, 155, 16, name, 12, "#1e1e2e", "left"))
    pct_x = cx_lbl + max(bw+5, 165)
    els.append(t(f"chv{j}", pct_x, cy+8, 100, 16, f"{n} ({pct}%)", 11, "#4a4569", "left"))

# PANEL 3: INDICADORES
els.append(t("s3c_lbl", 830, 498, 320, 16, "INDICADORES DE RETENCION", 11, "#6c6f85", "left"))
els.append(r("p3_bg", 830, 514, 320, 228, "#fff0f6", "#f783ac", 1))

indicadores = [
    ("#f38ba8", "22%",     "Rotacion Temprana",  "35 conductores retiran en <=30 dias"),
    ("#fab387", "52.7%",   "Tasa Reingreso",      "156/296 contratados habian estado antes"),
    ("#f9e2af", "Abr+Jul", "Meses Criticos",      "30 retiros c/u — maximo del periodo"),
    ("#a6e3a1", "Ene",     "Mejor Mes",           "46 contratados / 18 retiros = +28"),
    ("#89b4fa", "19 anos", "Max Antiguedad",       "Del Villar Castro — ingreso 2006"),
]
iy0 = 528; ih = 36; ig = 6; ix = 844
for j,(bg,val,lbl,sub) in enumerate(indicadores):
    iy = iy0 + j*(ih+ig)
    els.append(r(f"ind{j}", ix, iy, 295, ih, bg, "#1e1e2e", 1, 0, 100, True))
    els.append(t(f"indv{j}", ix+P, iy+4, 72, 18, val, 13, "#1e1e2e", "left"))
    els.append(t(f"indl{j}", ix+P+76, iy+4, 200, 16, lbl, 12, "#1e1e2e", "left"))
    els.append(t(f"inds{j}", ix+P+76, iy+20, 200, 13, sub, 9, "#6c6f85", "left"))

# FOOTER
els.append(t("footer", 50, 756, 1100, 14,
    "Datos: Procesos de reclutamiento.xlsx  |  LA CAROLINA BI  |  Generado 2026-05-26",
    10, "#adb5bd", "center"))

diagram = {
    "type": "excalidraw", "version": 2,
    "source": "https://excalidraw.com",
    "elements": els,
    "appState": {"gridSize": None, "viewBackgroundColor": "#f8f8f2"},
    "files": {}
}

path = "Wiki/assets/rrhh-rotacion-conductores-2025.excalidraw"
with open(path, "w", encoding="utf-8") as f:
    json.dump(diagram, f, ensure_ascii=False, indent=2)
print(f"OK  {path}  ({len(els)} elementos)")
