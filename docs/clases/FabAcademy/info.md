# Informacion general



<!-- === FAB Academy - Calculadora de Pagos === -->
<script>
(function () {
  const STATE_KEY = "fab_calc_state_v1";

  // Valores por defecto
  const defaults = {
    fab_usd: 2000,           // Costo del FAB en USD (constante)
    credito_mxn: 2600,       // Costo por crédito en MXN (constante)
    usd_mxn: 18.50,          // Tipo de cambio manual (editable, respaldo si falla el fetch)
    usar_fx_rt: true,        // Usar tipo de cambio en tiempo real
    margen_pct: 1.0,         // Margen % sobre el tipo de cambio (por ejemplo 1% = 1.0)
    creditos: 10,            // Créditos a revalidar (variable)
    beca_pct: 0              // Porcentaje de beca (0–100)
  };

  // Guardar/cargar estado
  function loadState() {
    try {
      const raw = localStorage.getItem(STATE_KEY);
      if (!raw) return { ...defaults };
      const data = JSON.parse(raw);
      return { ...defaults, ...data };
    } catch {
      return { ...defaults };
    }
  }
  function saveState(s) {
    try { localStorage.setItem(STATE_KEY, JSON.stringify(s)); } catch {}
  }

  // Formateadores
  const fmt = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 2 });
  const fmtUSD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

  // Cálculos
  function compute(state) {
    const fab_usd = clampNum(state.fab_usd, 0);
    const credito_mxn = clampNum(state.credito_mxn, 0);
    const creditos = clampNum(state.creditos, 0);
    const beca_pct = clampNum(state.beca_pct, 0, 100);
    const usd_mxn = clampNum(state.usd_mxn, 0);
    const margen_pct = clampNum(state.margen_pct, 0, 100);

    const tipo_cambio_aplicado = usd_mxn * (1 + margen_pct / 100);
    const fab_mxn = fab_usd * tipo_cambio_aplicado;

    const subtotal_creditos_mxn = credito_mxn * creditos;
    const factor_beca = (100 - beca_pct) / 100;
    const total_post_beca_mxn = subtotal_creditos_mxn * factor_beca;

    const pago_ibero_mxn = total_post_beca_mxn * 0.25; // 25%
    const descuento_fab_mxn = total_post_beca_mxn * 0.75; // 75%

    const diferencia_descuento_vs_fab_mxn = descuento_fab_mxn - fab_mxn;

    return {
      tipo_cambio_aplicado,
      fab_mxn,
      subtotal_creditos_mxn,
      total_post_beca_mxn,
      pago_ibero_mxn,
      descuento_fab_mxn,
      diferencia_descuento_vs_fab_mxn
    };
  }

  function clampNum(x, lo, hi) {
    x = Number(x);
    if (Number.isNaN(x)) x = 0;
    if (typeof lo === "number") x = Math.max(lo, x);
    if (typeof hi === "number") x = Math.min(hi, x);
    return x;
  }

  // Fetch tipo de cambio (cliente) — exchangerate.host suele tener CORS abierto
  async function fetchUSDMXN() {
    try {
      const res = await fetch("https://api.exchangerate.host/latest?base=USD&symbols=MXN", { cache: "no-store" });
      if (!res.ok) throw new Error("FX HTTP " + res.status);
      const data = await res.json();
      const rate = data && data.rates && data.rates.MXN;
      if (typeof rate === "number" && rate > 0) return rate;
      throw new Error("FX inválido");
    } catch (e) {
      console.warn("No se pudo obtener tipo de cambio en tiempo real:", e);
      return null;
    }
  }

  // Render
  function render(container, state, results) {
    const statusTxt = results.diferencia_descuento_vs_fab_mxn >= 0
      ? `✅ El descuento cubre el FAB y sobra ${fmt(results.diferencia_descuento_vs_fab_mxn)}.`
      : `⚠️ Falta ${fmt(Math.abs(results.diferencia_descuento_vs_fab_mxn))} para cubrir el FAB.`;

    container.querySelector("[data-out='usd_mxn_aplicado']").textContent = `${results.tipo_cambio_aplicado.toFixed(4)} MXN/USD`;
    container.querySelector("[data-out='fab_usd']").textContent = fmtUSD(state.fab_usd);
    container.querySelector("[data-out='fab_mxn']").textContent = fmt(results.fab_mxn);

    container.querySelector("[data-out='subtotal_creditos']").textContent = fmt(results.subtotal_creditos_mxn);
    container.querySelector("[data-out='post_beca']").textContent = fmt(results.total_post_beca_mxn);
    container.querySelector("[data-out='pago_ibero']").textContent = fmt(results.pago_ibero_mxn);
    container.querySelector("[data-out='desc_fab']").textContent = fmt(results.descuento_fab_mxn);

    container.querySelector("[data-out='diferencia']").textContent = fmt(results.diferencia_descuento_vs_fab_mxn);
    container.querySelector("[data-out='status']").textContent = statusTxt;

    // Mostrar/ocultar controles de FX
    container.querySelector("[data-row='fx_manual']").style.display = state.usar_fx_rt ? "none" : "";
    container.querySelector("[data-row='fx_margen']").style.display = state.usar_fx_rt ? "" : "";
  }

  // Inicializar UI
  function init() {
    const state = loadState();

    const root = document.getElementById("fab-calc");
    if (!root) return;

    // Inputs
    const $ = (sel) => root.querySelector(sel);

    // Set defaults
    $("[name='fab_usd']").value = state.fab_usd;
    $("[name='credito_mxn']").value = state.credito_mxn;
    $("[name='creditos']").value = state.creditos;
    $("[name='beca_pct']").value = state.beca_pct;
    $("[name='usar_fx_rt']").checked = state.usar_fx_rt;
    $("[name='usd_mxn']").value = state.usd_mxn;
    $("[name='margen_pct']").value = state.margen_pct;

    // Recalcular
    async function recalc({ tryFetch = false } = {}) {
      // Actualiza estado desde UI
      state.fab_usd = Number($("[name='fab_usd']").value);
      state.credito_mxn = Number($("[name='credito_mxn']").value);
      state.creditos = Number($("[name='creditos']").value);
      state.beca_pct = Number($("[name='beca_pct']").value);
      state.usar_fx_rt = $("[name='usar_fx_rt']").checked;
      state.usd_mxn = Number($("[name='usd_mxn']").value);
      state.margen_pct = Number($("[name='margen_pct']").value);

      // Intentar FX en tiempo real si está habilitado
      if (state.usar_fx_rt && tryFetch) {
        const live = await fetchUSDMXN();
        if (live) {
          state.usd_mxn = live;               // Guardamos el valor "base" en el campo (oculto)
          $("[name='usd_mxn']").value = live; // para que quede persistido
        }
      }

      saveState(state);
      const results = compute(state);
      render(root, state, results);
    }

    // Listeners
    root.addEventListener("input", (e) => {
      if (e.target && e.target.matches("input")) recalc();
    });
    // Botón actualizar FX
    $("[data-action='update-fx']").addEventListener("click", () => recalc({ tryFetch: true }));

    // Primer render
    recalc({ tryFetch: true });
  }

  // Esperar a que MkDocs cargue
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(() => setTimeout(init, 0));
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>

<style>
.fab-grid { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.fab-card { border: 1px solid var(--md-default-fg-color--lightest, #ddd); border-radius: .75rem; padding: 1rem; }
.fab-row { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
.fab-row label { font-weight: 600; }
.fab-num { width: 120px; }
.fab-help { font-size: .9em; opacity: .75; }
.fab-table { width: 100%; border-collapse: collapse; }
.fab-table th, .fab-table td { padding: .5rem; border-bottom: 1px solid #e5e7eb; text-align: right; }
.fab-table th:first-child, .fab-table td:first-child { text-align: left; }
.fab-status { font-weight: 700; }
</style>

<div id="fab-calc" class="fab-grid">

  <!-- Parámetros -->
  <div class="fab-card">
    <h3>Parámetros</h3>
    <div class="fab-row">
      <label for="fab_usd">Costo FAB (USD):</label>
      <input class="fab-num" type="number" name="fab_usd" id="fab_usd" step="1" min="0">
    </div>
    <div class="fab-row">
      <label for="credito_mxn">Costo por crédito (MXN):</label>
      <input class="fab-num" type="number" name="credito_mxn" id="credito_mxn" step="1" min="0">
    </div>
    <div class="fab-row">
      <label for="creditos">Créditos a revalidar:</label>
      <input class="fab-num" type="number" name="creditos" id="creditos" step="1" min="0">
    </div>
    <div class="fab-row">
      <label for="beca_pct">Beca (%):</label>
      <input class="fab-num" type="number" name="beca_pct" id="beca_pct" step="0.5" min="0" max="100">
    </div>
  </div>

  <!-- Tipo de cambio -->
  <div class="fab-card">
    <h3>Tipo de cambio</h3>
    <div class="fab-row">
      <label for="usar_fx_rt">Usar tipo de cambio en tiempo real</label>
      <input type="checkbox" name="usar_fx_rt" id="usar_fx_rt">
    </div>
    <div class="fab-row" data-row="fx_margen">
      <span>Margen sobre FX en tiempo real (%)</span>
      <input class="fab-num" type="number" name="margen_pct" step="0.1" min="0">
    </div>
    <div class="fab-row" data-row="fx_manual">
      <span>Tipo de cambio manual (USD→MXN)</span>
      <input class="fab-num" type="number" name="usd_mxn" step="0.0001" min="0">
    </div>
    <div class="fab-row">
      <button type="button" data-action="update-fx">Actualizar tipo de cambio</button>
      <span class="fab-help">Se usa <code>exchangerate.host</code> si está disponible.</span>
    </div>
    <div class="fab-row">
      <span>Tipo de cambio aplicado (con margen):</span>
      <strong data-out="usd_mxn_aplicado">—</strong>
    </div>
  </div>

  <!-- Resultados -->
  <div class="fab-card" style="grid-column: 1 / -1;">
    <h3>Resultados</h3>
    <table class="fab-table">
      <thead>
        <tr>
          <th>Concepto</th>
          <th>Monto</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Costo FAB</td>
          <td><span data-out="fab_usd">—</span> / <span data-out="fab_mxn">—</span></td>
        </tr>
        <tr>
          <td>Subtotal créditos (antes de beca)</td>
          <td><span data-out="subtotal_creditos">—</span></td>
        </tr>
        <tr>
          <td>Total tras beca</td>
          <td><span data-out="post_beca">—</span></td>
        </tr>
        <tr>
          <td>Pago a IBERO (25%)</td>
          <td><span data-out="pago_ibero">—</span></td>
        </tr>
        <tr>
          <td>Descuento para pagar FAB (75%)</td>
          <td><span data-out="desc_fab">—</span></td>
        </tr>
        <tr>
          <td>Diferencia (descuento − costo FAB)</td>
          <td><span data-out="diferencia">—</span></td>
        </tr>
      </tbody>
    </table>
    <p class="fab-status" data-out="status">—</p>
    <p class="fab-help">
      Fórmulas:<br>
      <code>post_beca = (créditos × costo_crédito) × (1 − beca%)</code><br>
      <code>IBERO = post_beca × 0.25</code>&nbsp;&nbsp;·&nbsp;&nbsp;<code>Descuento FAB = post_beca × 0.75</code><br>
      <code>FAB_MXN = FAB_USD × (TC × (1 + margen%))</code><br>
      <code>Diferencia = Descuento FAB − FAB_MXN</code>
    </p>
  </div>
</div>
