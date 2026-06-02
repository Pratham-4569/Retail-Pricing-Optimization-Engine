/* ====================================================
   RetailIQ Executive Dashboard — Application Logic
   ==================================================== */

// ─── Color Palette ──────────────────────────────────
const COLORS = ['#667eea','#764ba2','#00d2ff','#48bb78','#ecc94b','#fc8181','#ed64a6','#4fd1c5'];
const COLORS_ALPHA = a => COLORS.map(c => c + Math.round(a*255).toString(16).padStart(2,'0'));

// ─── Number Formatting (Indian) ─────────────────────
function formatINR(n, compact) {
    if (n == null || isNaN(n)) return '—';
    const abs = Math.abs(n);
    if (compact && abs >= 1e7) return '₹' + (n/1e7).toFixed(2) + ' Cr';
    if (compact && abs >= 1e5) return '₹' + (n/1e5).toFixed(2) + ' L';
    // Indian grouping: last 3 digits, then groups of 2
    const parts = n.toFixed(0).split('.');
    let intPart = parts[0];
    const sign = intPart.startsWith('-') ? '-' : '';
    intPart = intPart.replace('-','');
    if (intPart.length > 3) {
        const last3 = intPart.slice(-3);
        let rest = intPart.slice(0, -3);
        rest = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
        intPart = rest + ',' + last3;
    }
    return '₹' + sign + intPart;
}
function formatPct(n) { return n == null ? '—' : (n >= 0 ? '+' : '') + n.toFixed(1) + '%'; }
function formatUnits(n) { return n == null ? '—' : Math.round(n).toLocaleString('en-IN'); }
function shortINR(n) { return formatINR(n, true); }

// ─── Chart.js Defaults ──────────────────────────────
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#a0aec0';
Chart.defaults.plugins.legend.display = false;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15,15,35,0.95)';
Chart.defaults.plugins.tooltip.titleColor = '#fff';
Chart.defaults.plugins.tooltip.bodyColor = '#a0aec0';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 10;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.displayColors = true;
Chart.defaults.plugins.tooltip.boxPadding = 4;
Chart.defaults.scale.grid = { color: 'rgba(255,255,255,0.04)', drawBorder: false };
Chart.defaults.scale.ticks = { color: '#718096', font: { size: 11 } };
Chart.defaults.elements.bar.borderRadius = 6;
Chart.defaults.animation.duration = 900;
Chart.defaults.animation.easing = 'easeOutQuart';

// ─── Comprehensive Sample Data ──────────────────────
const SAMPLE_DATA = buildSampleData();

function buildSampleData() {
    const categories = ['Electronics','Apparel','Home & Kitchen','Beauty & Personal Care','Sports & Fitness','Grocery & Gourmet'];
    const months = [];
    for (let i = 23; i >= 0; i--) {
        const d = new Date(); d.setMonth(d.getMonth() - i);
        months.push(d.toISOString().slice(0,7));
    }

    // Monthly trends
    const monthlyTrends = months.map((m,i) => {
        const base = 4200000 + Math.sin(i/4)*800000 + i*60000;
        const rev = Math.round(base + (Math.random()-.4)*400000);
        const prof = Math.round(rev * (0.18 + Math.random()*0.08));
        const orders = Math.round(rev / (850 + Math.random()*400));
        return { month: m, revenue: rev, profit: prof, orders };
    });

    // Products
    const productNames = {
        'Electronics': ['Samsung Galaxy M34 5G','boAt Rockerz 450','Noise ColorFit Pro 4','Redmi 12 5G','OnePlus Nord Buds 2','Fire-Boltt Phoenix','Ambrane PowerLit','JBL Tune 230NC','Realme Narzo 60','Mi Power Bank 20000'],
        'Apparel': ['Allen Solly Polo T-shirt','Levi\'s 511 Slim Jeans','Van Heusen Formal Shirt','Peter England Chinos','US Polo Oxford Shoes','Wildcraft Rain Jacket','Jockey Track Pants','Raymond Blazer','Puma Running Shorts','Nike Dri-FIT Tee'],
        'Home & Kitchen': ['Prestige Induction Cooktop','Pigeon Kettle 1.5L','Milton Thermosteel Flask','Havells Mixer Grinder','Cello Opalware Set','Wipro LED Bulb Pack','AmazonBasics Bedsheet','Solimo Non-stick Pan','Philips Air Fryer','Borosil Casserole'],
        'Beauty & Personal Care': ['Mamaearth Vitamin C Serum','Biotique Bio Neem Facewash','L\'Oréal Paris Shampoo','Nivea Body Lotion','Himalaya Face Cream','Gillette Mach3 Razor','Dove Bar Soap Pack','Lakme Eyeconic Kajal','Forest Essentials Oil','The Man Company Beard Kit'],
        'Sports & Fitness': ['Boldfit Yoga Mat','Nivia Storm Football','Strauss Dumbbells 5kg','Adidas Training Gloves','Vector X Cricket Bat','Cosco Badminton Racket','Fitkit Resistance Band','JELEX Skipping Rope','Nivia Running Shoes','Puma Gym Bag'],
        'Grocery & Gourmet': ['Tata Sampann Dal 1kg','Aashirvaad Atta 5kg','Saffola Gold Oil 5L','Cadbury Celebrations Pack','Sundrop Peanut Butter','Organic Tattva Honey','Paper Boat Aamras 6pk','Too Yumm Multigrain','Society Tea Premium','Nescafé Classic Coffee']
    };

    const products = [];
    let pid = 1;
    for (const cat of categories) {
        const names = productNames[cat];
        for (let j = 0; j < names.length; j++) {
            const priceBase = cat === 'Electronics' ? 1200 + Math.random()*14000 :
                              cat === 'Apparel' ? 500 + Math.random()*4500 :
                              cat === 'Home & Kitchen' ? 300 + Math.random()*6000 :
                              cat === 'Beauty & Personal Care' ? 150 + Math.random()*2500 :
                              cat === 'Sports & Fitness' ? 200 + Math.random()*3000 :
                              100 + Math.random()*1500;
            const price = Math.round(priceBase);
            const cost = Math.round(price * (0.52 + Math.random()*0.2));
            const units = Math.round(80 + Math.random()*920);
            const revenue = price * units;
            const profit = (price - cost) * units;
            const margin = ((price - cost) / price) * 100;
            products.push({
                id: pid++, name: names[j], category: cat,
                price, cost, units, revenue, profit,
                margin: Math.round(margin*10)/10
            });
        }
    }

    // Category revenue for donut
    const categoryRevenue = {};
    for (const p of products) {
        categoryRevenue[p.category] = (categoryRevenue[p.category]||0) + p.revenue;
    }

    // Forecast data
    const forecastMonths = [];
    for (let i = 1; i <= 3; i++) {
        const d = new Date(); d.setMonth(d.getMonth() + i);
        forecastMonths.push(d.toISOString().slice(0,7));
    }
    const lastDemand = monthlyTrends.slice(-6).map(m=>m.orders);
    const avgDemand = lastDemand.reduce((a,b)=>a+b,0)/lastDemand.length;
    const forecastData = {
        historical: monthlyTrends.map(m => ({ month: m.month, demand: m.orders })),
        forecast: forecastMonths.map((m,i) => {
            const pred = Math.round(avgDemand * (1 + 0.03*(i+1)) + (Math.random()-.5)*300);
            return { month: m, demand: pred, lower: Math.round(pred*0.85), upper: Math.round(pred*1.15) };
        }),
        accuracy: 92.4, mape: 7.6, rmse: 312,
        byCategory: {}
    };
    for (const cat of categories) {
        const catProducts = products.filter(p=>p.category===cat);
        const catUnits = catProducts.reduce((s,p)=>s+p.units,0);
        forecastData.byCategory[cat] = {
            historical: months.map((m,i) => ({ month: m, demand: Math.round(catUnits/12*(0.7+Math.random()*0.6) + Math.sin(i/3)*catUnits/40) })),
            forecast: forecastMonths.map((m,i) => {
                const pred = Math.round(catUnits/12*(1+0.02*(i+1)) + (Math.random()-.5)*catUnits/20);
                return { month: m, demand: pred, lower: Math.round(pred*0.82), upper: Math.round(pred*1.18) };
            })
        };
    }

    // Elasticity
    const elasticity = {
        'Electronics':             { value: -1.82, label: 'Highly Elastic' },
        'Apparel':                 { value: -1.45, label: 'Elastic' },
        'Home & Kitchen':          { value: -0.78, label: 'Inelastic' },
        'Beauty & Personal Care':  { value: -0.92, label: 'Near Unit Elastic' },
        'Sports & Fitness':        { value: -1.23, label: 'Elastic' },
        'Grocery & Gourmet':       { value: -0.35, label: 'Highly Inelastic' }
    };

    // Recommendations
    const recommendations = products.map(p => {
        const e = Math.abs(elasticity[p.category].value);
        const inventoryPressure = Math.random();
        let discount = 0;
        if (p.margin > 30 && inventoryPressure > 0.4) {
            discount = Math.round((5 + e*6 + inventoryPressure*10) * 10) / 10;
        } else if (p.margin > 20) {
            discount = Math.round((3 + e*3 + inventoryPressure*5) * 10) / 10;
        } else {
            discount = Math.round((1 + e*2) * 10) / 10;
        }
        discount = Math.min(discount, 40);
        const newPrice = Math.round(p.price * (1 - discount/100));
        const demandLift = 1 + (discount/100) * e;
        const newUnits = Math.round(p.units * demandLift);
        const expRevenue = newPrice * newUnits;
        const expProfit = (newPrice - p.cost) * newUnits;
        const clearance = Math.min(100, Math.round(50 + inventoryPressure*50));
        return {
            id: p.id, name: p.name, category: p.category,
            currentPrice: p.price, discount, newPrice,
            expRevenue, expProfit, clearance,
            baseUnits: p.units, baseDemandLift: demandLift
        };
    });

    return { categories, months, monthlyTrends, products, categoryRevenue, forecastData, elasticity, recommendations };
}

// ─── App State ──────────────────────────────────────
const state = {
    data: null,
    charts: {},
    sortState: {},  // { tableId: { key, dir } }
};

// ─── Init ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    state.data = await loadData();
    hideLoader();
    renderAll();
    initNavigation();
    initSearch();
    initSliders();
    setFooterTimestamp();
});

async function loadData() {
    // Try loading from ../output/ first; fallback to sample data
    const files = [
        { key: 'monthlyTrends',   path: '../output/monthly_trends.json' },
        { key: 'products',        path: '../output/products.json' },
        { key: 'categoryRevenue', path: '../output/category_revenue.json' },
        { key: 'forecastData',    path: '../output/forecast.json' },
        { key: 'elasticity',      path: '../output/elasticity.json' },
        { key: 'recommendations', path: '../output/recommendations.json' }
    ];
    const data = { ...SAMPLE_DATA };
    for (const f of files) {
        try {
            const res = await fetch(f.path);
            if (res.ok) { data[f.key] = await res.json(); }
        } catch (_) { /* fallback to sample */ }
    }
    return data;
}

function hideLoader() {
    setTimeout(() => document.getElementById('loading-overlay').classList.add('hidden'), 1200);
}

function setFooterTimestamp() {
    const now = new Date();
    document.getElementById('footer-timestamp').textContent =
        now.toLocaleDateString('en-IN', { day:'numeric', month:'long', year:'numeric' }) +
        ' • ' + now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
}

// ─── Render All ─────────────────────────────────────
function renderAll() {
    renderKPIs();
    renderRevenueProfit();
    renderCategoryDonut();
    renderBestSellers();
    renderWorstSellers();
    renderCategoryPerformance();
    renderProductTable();
    renderForecast();
    renderElasticity();
    renderPriceDemandCurve();
    renderElasticityCards();
    renderRecommendations();
    renderWhatIfTable();
    updateWhatIfKPIs();
}

// ─── 1. KPIs ────────────────────────────────────────
function renderKPIs() {
    const d = state.data;
    const trends = d.monthlyTrends;
    const latest = trends[trends.length - 1];
    const prev   = trends[trends.length - 2];

    animateValue('kpi-revenue', 0, latest.revenue, 1200, formatINR);
    animateValue('kpi-profit',  0, latest.profit,  1200, formatINR);
    animateValue('kpi-orders',  0, latest.orders,  1200, formatUnits);
    const aov = latest.revenue / latest.orders;
    animateValue('kpi-aov', 0, aov, 1200, formatINR);

    setTrend('kpi-revenue-trend', latest.revenue, prev.revenue);
    setTrend('kpi-profit-trend',  latest.profit,  prev.profit);
    setTrend('kpi-orders-trend',  latest.orders,  prev.orders);
    setTrend('kpi-aov-trend', latest.revenue/latest.orders, prev.revenue/prev.orders);

    drawSparkline('spark-revenue', trends.map(t=>t.revenue), '#667eea');
    drawSparkline('spark-profit',  trends.map(t=>t.profit),  '#48bb78');
    drawSparkline('spark-orders',  trends.map(t=>t.orders),  '#00d2ff');
    drawSparkline('spark-aov',     trends.map(t=>t.revenue/t.orders), '#ecc94b');
}

function animateValue(elId, from, to, dur, fmt) {
    const el = document.getElementById(elId);
    if (!el) return;
    const start = performance.now();
    const step = ts => {
        const p = Math.min((ts - start) / dur, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(from + (to - from) * ease);
        if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

function setTrend(elId, cur, prev) {
    const el = document.getElementById(elId);
    if (!el) return;
    const pct = ((cur - prev) / prev * 100);
    const arrow = el.querySelector('.trend-arrow');
    const val = el.querySelector('.trend-val');
    if (pct > 0) { el.className = 'kpi-trend up'; arrow.textContent = '↑'; }
    else if (pct < 0) { el.className = 'kpi-trend down'; arrow.textContent = '↓'; }
    else { el.className = 'kpi-trend flat'; arrow.textContent = '→'; }
    val.textContent = Math.abs(pct).toFixed(1) + '%';
}

function drawSparkline(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const last12 = data.slice(-12);
    const min = Math.min(...last12), max = Math.max(...last12);
    const range = max - min || 1;
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    last12.forEach((v,i) => {
        const x = (i/(last12.length-1))*w;
        const y = h - ((v-min)/range)*(h-4) - 2;
        i === 0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
    });
    ctx.stroke();
    // area fill
    const lastX = w, lastY = h - ((last12[last12.length-1]-min)/range)*(h-4) - 2;
    ctx.lineTo(lastX, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0,0,0,h);
    grad.addColorStop(0, color + '30');
    grad.addColorStop(1, color + '00');
    ctx.fillStyle = grad;
    ctx.fill();
}

// ─── 2. Revenue vs Profit Chart ─────────────────────
function renderRevenueProfit() {
    const d = state.data;
    const last12 = d.monthlyTrends.slice(-12);
    const labels = last12.map(m => {
        const [y,mo] = m.month.split('-');
        return new Date(y, mo-1).toLocaleString('en-IN',{month:'short',year:'2-digit'});
    });
    const ctx = document.getElementById('chart-revenue-profit');
    state.charts.revenueProfit = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: last12.map(m => m.revenue),
                    backgroundColor: createGradientBar(ctx, '#667eea','#764ba2'),
                    borderRadius: 8, borderSkipped: false,
                    barPercentage: 0.6, categoryPercentage: 0.7
                },
                {
                    label: 'Profit',
                    data: last12.map(m => m.profit),
                    backgroundColor: createGradientBar(ctx, '#48bb78','#38a169'),
                    borderRadius: 8, borderSkipped: false,
                    barPercentage: 0.6, categoryPercentage: 0.7
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            plugins: {
                legend: { display: true, position: 'top', align: 'end',
                    labels: { usePointStyle: true, pointStyle: 'rectRounded', padding: 16, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: { label: ctx2 => ctx2.dataset.label + ': ' + formatINR(ctx2.raw) }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => shortINR(v) } }
            }
        }
    });
}

function createGradientBar(canvas, c1, c2) {
    const el = canvas.getContext ? canvas : canvas.canvas || canvas;
    const ctx2 = el.getContext ? el.getContext('2d') : el;
    const grad = ctx2.createLinearGradient(0, 0, 0, 300);
    grad.addColorStop(0, c1);
    grad.addColorStop(1, c2 + '99');
    return grad;
}

// ─── 3. Category Donut ──────────────────────────────
function renderCategoryDonut() {
    const d = state.data;
    const cats = Object.keys(d.categoryRevenue);
    const vals = Object.values(d.categoryRevenue);
    const ctx = document.getElementById('chart-category-donut');
    state.charts.categoryDonut = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: cats,
            datasets: [{
                data: vals,
                backgroundColor: COLORS.slice(0, cats.length),
                borderColor: '#0a0a1a',
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            cutout: '68%',
            plugins: {
                legend: {
                    display: true, position: 'right',
                    labels: { usePointStyle: true, pointStyle: 'circle', padding: 14, font: { size: 11 }, color: '#a0aec0' }
                },
                tooltip: {
                    callbacks: { label: ctx2 => {
                        const total = vals.reduce((a,b)=>a+b,0);
                        return ctx2.label + ': ' + formatINR(ctx2.raw) + ' (' + (ctx2.raw/total*100).toFixed(1) + '%)';
                    }}
                }
            }
        }
    });
}

// ─── 4. Best / Worst Sellers ────────────────────────
function renderBestSellers() {
    const sorted = [...state.data.products].sort((a,b) => b.revenue - a.revenue).slice(0,10).reverse();
    const ctx = document.getElementById('chart-best-sellers');
    state.charts.bestSellers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(p => truncate(p.name, 22)),
            datasets: [{
                data: sorted.map(p => p.revenue),
                backgroundColor: sorted.map((_,i) => COLORS[i % COLORS.length] + 'cc'),
                borderRadius: 6, borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {
                tooltip: { callbacks: { label: ctx2 => 'Revenue: ' + formatINR(ctx2.raw) } }
            },
            scales: {
                x: { ticks: { callback: v => shortINR(v) } },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

function renderWorstSellers() {
    const sorted = [...state.data.products].sort((a,b) => a.revenue - b.revenue).slice(0,10).reverse();
    const ctx = document.getElementById('chart-worst-sellers');
    state.charts.worstSellers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(p => truncate(p.name, 22)),
            datasets: [{
                data: sorted.map(p => p.revenue),
                backgroundColor: sorted.map((_,i) => {
                    const t = i / 9;
                    return `rgba(252,129,129,${0.4 + t*0.5})`;
                }),
                borderRadius: 6, borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {
                tooltip: { callbacks: { label: ctx2 => 'Revenue: ' + formatINR(ctx2.raw) } }
            },
            scales: {
                x: { ticks: { callback: v => shortINR(v) } },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

// ─── 5. Category Performance ────────────────────────
function renderCategoryPerformance() {
    const d = state.data;
    const cats = d.categories;
    const catData = cats.map(cat => {
        const prods = d.products.filter(p => p.category === cat);
        return {
            revenue: prods.reduce((s,p) => s+p.revenue, 0),
            profit: prods.reduce((s,p) => s+p.profit, 0),
            units: prods.reduce((s,p) => s+p.units, 0)
        };
    });
    const ctx = document.getElementById('chart-category-performance');
    state.charts.catPerf = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cats.map(c => truncate(c, 18)),
            datasets: [
                { label: 'Revenue', data: catData.map(c=>c.revenue), backgroundColor: '#667eea', borderRadius: 6 },
                { label: 'Profit',  data: catData.map(c=>c.profit),  backgroundColor: '#48bb78', borderRadius: 6 },
                { label: 'Units',   data: catData.map(c=>c.units),   backgroundColor: '#ecc94b', borderRadius: 6, yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            plugins: {
                legend: { display: true, position: 'top', align: 'end',
                    labels: { usePointStyle: true, pointStyle: 'rectRounded', padding: 16, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx2 => {
                            const v = ctx2.raw;
                            return ctx2.dataset.label + ': ' + (ctx2.dataset.label === 'Units' ? formatUnits(v) : formatINR(v));
                        }
                    }
                }
            },
            scales: {
                y:  { beginAtZero: true, ticks: { callback: v => shortINR(v) }, position: 'left' },
                y1: { beginAtZero: true, ticks: { callback: v => formatUnits(v) }, position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
}

// ─── 6. Product Table ───────────────────────────────
function renderProductTable() {
    const tbody = document.getElementById('product-table-body');
    const prods = [...state.data.products].sort((a,b) => b.revenue - a.revenue);
    tbody.innerHTML = prods.map(p => `
        <tr>
            <td class="fw-700">${p.name}</td>
            <td>${p.category}</td>
            <td>${formatINR(p.price)}</td>
            <td>${formatINR(p.revenue)}</td>
            <td class="${p.profit > 0 ? 'text-success' : 'text-danger'}">${formatINR(p.profit)}</td>
            <td>${formatUnits(p.units)}</td>
            <td><span class="${p.margin > 30 ? 'text-success' : p.margin > 15 ? 'text-warning' : 'text-danger'}">${p.margin.toFixed(1)}%</span></td>
        </tr>
    `).join('');
    initTableSort('product-table', prods, renderProductTableRows);
}

function renderProductTableRows(prods) {
    const tbody = document.getElementById('product-table-body');
    tbody.innerHTML = prods.map(p => `
        <tr>
            <td class="fw-700">${p.name}</td>
            <td>${p.category}</td>
            <td>${formatINR(p.price)}</td>
            <td>${formatINR(p.revenue)}</td>
            <td class="${p.profit > 0 ? 'text-success' : 'text-danger'}">${formatINR(p.profit)}</td>
            <td>${formatUnits(p.units)}</td>
            <td><span class="${p.margin > 30 ? 'text-success' : p.margin > 15 ? 'text-warning' : 'text-danger'}">${p.margin.toFixed(1)}%</span></td>
        </tr>
    `).join('');
}

// ─── 7. Forecast ────────────────────────────────────
function renderForecast(category) {
    const d = state.data.forecastData;
    const cat = category || 'all';

    // Populate category dropdown once
    const sel = document.getElementById('forecast-category-select');
    if (sel.options.length <= 1) {
        state.data.categories.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c; opt.textContent = c;
            sel.appendChild(opt);
        });
        sel.addEventListener('change', () => renderForecast(sel.value === 'all' ? null : sel.value));
    }

    let hist, fore;
    if (cat === 'all' || !d.byCategory[cat]) {
        hist = d.historical;
        fore = d.forecast;
    } else {
        hist = d.byCategory[cat].historical;
        fore = d.byCategory[cat].forecast;
    }

    const allLabels = [...hist.map(h=>h.month), ...fore.map(f=>f.month)];
    const displayLabels = allLabels.map(m => {
        const [y,mo] = m.split('-');
        return new Date(y, mo-1).toLocaleString('en-IN',{month:'short', year:'2-digit'});
    });

    const histData = hist.map(h => h.demand);
    const foreData = [...new Array(hist.length).fill(null), ...fore.map(f => f.demand)];
    const upperData = [...new Array(hist.length).fill(null), ...fore.map(f => f.upper)];
    const lowerData = [...new Array(hist.length).fill(null), ...fore.map(f => f.lower)];

    // Bridge: connect the last historical point to first forecast
    if (hist.length > 0 && fore.length > 0) {
        foreData[hist.length - 1] = histData[histData.length - 1];
    }

    if (state.charts.forecast) state.charts.forecast.destroy();
    const ctx = document.getElementById('chart-forecast');
    state.charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: displayLabels,
            datasets: [
                {
                    label: 'Historical Demand',
                    data: histData.concat(new Array(fore.length).fill(null)),
                    borderColor: '#667eea',
                    backgroundColor: '#667eea22',
                    fill: false,
                    tension: 0.35, pointRadius: 2, pointHoverRadius: 5,
                    borderWidth: 2.5
                },
                {
                    label: 'Forecast',
                    data: foreData,
                    borderColor: '#00d2ff',
                    borderDash: [8, 4],
                    fill: false,
                    tension: 0.35, pointRadius: 4, pointHoverRadius: 6,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#00d2ff'
                },
                {
                    label: 'Upper Bound',
                    data: upperData,
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(0,210,255,0.08)',
                    fill: '+1', pointRadius: 0, borderWidth: 0
                },
                {
                    label: 'Lower Bound',
                    data: lowerData,
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(0,210,255,0.08)',
                    fill: '-1', pointRadius: 0, borderWidth: 0
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: { label: ctx2 => {
                        if (ctx2.dataset.label === 'Upper Bound' || ctx2.dataset.label === 'Lower Bound') return null;
                        return ctx2.dataset.label + ': ' + formatUnits(ctx2.raw);
                    }}
                }
            },
            scales: {
                y: { beginAtZero: false, ticks: { callback: v => formatUnits(v) } }
            }
        }
    });

    // Metrics
    document.getElementById('forecast-accuracy').textContent = d.accuracy + '%';
    document.getElementById('forecast-mape').textContent = d.mape + '%';
    document.getElementById('forecast-rmse').textContent = formatUnits(d.rmse);
}

// ─── 8. Elasticity ──────────────────────────────────
function renderElasticity() {
    const d = state.data.elasticity;
    const cats = Object.keys(d);
    const vals = cats.map(c => Math.abs(d[c].value));
    const bgColors = vals.map(v => v > 1.5 ? '#fc8181cc' : v > 1 ? '#ecc94bcc' : '#48bb78cc');

    const ctx = document.getElementById('chart-elasticity');
    state.charts.elasticity = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cats.map(c => truncate(c, 20)),
            datasets: [{
                label: 'Price Elasticity |E|',
                data: vals,
                backgroundColor: bgColors,
                borderRadius: 8, borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx2 => {
                            const cat = cats[ctx2.dataIndex];
                            return `|E| = ${d[cat].value.toFixed(2)} — ${d[cat].label}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { callback: v => v.toFixed(1) },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                }
            }
        }
    });
}

function renderPriceDemandCurve() {
    // Simulated price-demand curves for top 2 categories
    const d = state.data.elasticity;
    const cats = Object.keys(d).slice(0, 3);
    const datasets = cats.map((cat, i) => {
        const e = d[cat].value;
        const baseP = 1000; const baseQ = 500;
        const points = [];
        for (let dp = -40; dp <= 60; dp += 5) {
            const p = baseP * (1 + dp/100);
            const q = Math.max(0, baseQ * Math.pow(p/baseP, e));
            points.push({ x: p, y: Math.round(q) });
        }
        return {
            label: cat,
            data: points,
            borderColor: COLORS[i],
            backgroundColor: COLORS[i] + '20',
            fill: false,
            tension: 0.4, pointRadius: 0, pointHoverRadius: 5,
            borderWidth: 2.5
        };
    });

    const ctx = document.getElementById('chart-price-demand');
    state.charts.priceDemand = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true, position: 'top',
                    labels: { usePointStyle: true, pointStyle: 'line', padding: 14, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        title: items => 'Price: ' + formatINR(items[0].raw.x),
                        label: ctx2 => ctx2.dataset.label + ': ' + formatUnits(ctx2.raw.y) + ' units'
                    }
                }
            },
            scales: {
                x: { type: 'linear', title: { display: true, text: 'Price (₹)', color: '#718096' }, ticks: { callback: v => '₹'+v } },
                y: { title: { display: true, text: 'Demand (Units)', color: '#718096' }, beginAtZero: true }
            }
        }
    });
}

function renderElasticityCards() {
    const d = state.data.elasticity;
    const container = document.getElementById('elasticity-cards');
    container.innerHTML = Object.entries(d).map(([cat, info], i) => {
        const abs = Math.abs(info.value);
        const cls = abs > 1 ? 'elastic' : abs > 0.9 ? 'unit' : 'inelastic';
        const desc = abs > 1.5 ? 'Price changes have a strong impact on demand. Discounts will significantly boost volume.' :
                     abs > 1   ? 'Demand is sensitive to price. Moderate discounts can drive meaningful sales lifts.' :
                     abs > 0.8 ? 'Demand is relatively stable with price changes. Focus on margin over volume.' :
                                 'Very stable demand. Pricing power is strong — avoid unnecessary discounts.';
        return `
            <div class="elast-card" style="--delay: ${0.1*i}s">
                <div class="elast-indicator ${cls}"></div>
                <div class="elast-card-body">
                    <div class="elast-card-title">${cat}</div>
                    <div class="elast-card-val ${abs > 1 ? 'text-danger' : 'text-success'}">${info.value.toFixed(2)} — ${info.label}</div>
                    <div class="elast-card-desc">${desc}</div>
                </div>
            </div>
        `;
    }).join('');
}

// ─── 9. Recommendations ─────────────────────────────
function renderRecommendations() {
    const recs = state.data.recommendations;
    const withDiscount = recs.filter(r => r.discount > 0);
    const avgDisc = withDiscount.reduce((s,r) => s+r.discount, 0) / (withDiscount.length || 1);
    const totalUplift = withDiscount.reduce((s,r) => s + (r.expRevenue - r.currentPrice * r.baseUnits), 0);

    document.getElementById('rec-count').textContent = withDiscount.length;
    document.getElementById('rec-avg-discount').textContent = avgDisc.toFixed(1) + '%';
    document.getElementById('rec-uplift').textContent = shortINR(totalUplift);

    renderRecTableRows(recs);
    initTableSort('rec-table', recs, renderRecTableRows);
}

function renderRecTableRows(recs) {
    const tbody = document.getElementById('rec-table-body');
    tbody.innerHTML = recs.map(r => {
        const discCls = r.discount <= 10 ? 'low' : r.discount <= 25 ? 'medium' : 'high';
        return `
        <tr>
            <td class="fw-700">${r.name}</td>
            <td>${r.category}</td>
            <td>${formatINR(r.currentPrice)}</td>
            <td><span class="discount-badge ${discCls}">${r.discount.toFixed(1)}%</span></td>
            <td>${formatINR(r.newPrice)}</td>
            <td>${formatINR(r.expRevenue)}</td>
            <td class="${r.expProfit > 0 ? 'text-success' : 'text-danger'}">${formatINR(r.expProfit)}</td>
            <td>
                <div class="clearance-bar"><div class="clearance-bar-fill" style="width:${r.clearance}%"></div></div>
                <span class="text-muted" style="margin-left:6px; font-size:.78rem">${r.clearance}%</span>
            </td>
        </tr>`;
    }).join('');
}

// ─── 10. What-If ────────────────────────────────────
function initSliders() {
    const sliders = ['demand','inventory','competitor'];
    sliders.forEach(s => {
        const el = document.getElementById(`slider-${s}`);
        const valEl = document.getElementById(`slider-${s}-val`);
        el.addEventListener('input', debounce(() => {
            const v = parseInt(el.value);
            valEl.textContent = (v >= 0 ? '+' : '') + v + '%';
            recalcWhatIf();
        }, 60));
        // Set initial gradient for track
        updateSliderTrack(el);
        el.addEventListener('input', () => updateSliderTrack(el));
    });
    document.getElementById('whatif-reset').addEventListener('click', () => {
        sliders.forEach(s => {
            const el = document.getElementById(`slider-${s}`);
            el.value = 0;
            document.getElementById(`slider-${s}-val`).textContent = '0%';
            updateSliderTrack(el);
        });
        recalcWhatIf();
    });
}

function updateSliderTrack(el) {
    const min = parseFloat(el.min), max = parseFloat(el.max), val = parseFloat(el.value);
    const pct = ((val - min) / (max - min)) * 100;
    el.style.background = `linear-gradient(to right, #667eea ${pct}%, rgba(255,255,255,0.08) ${pct}%)`;
}

function recalcWhatIf() {
    const demandChange = parseInt(document.getElementById('slider-demand').value) / 100;
    const invChange = parseInt(document.getElementById('slider-inventory').value) / 100;
    const compChange = parseInt(document.getElementById('slider-competitor').value) / 100;

    const recs = state.data.recommendations;
    const elast = state.data.elasticity;
    const baseRevenue = recs.reduce((s,r) => s + r.currentPrice * r.baseUnits, 0);
    const baseProfit = recs.reduce((s,r) => s + (r.currentPrice - (state.data.products.find(p=>p.id===r.id)?.cost || r.currentPrice*0.6)) * r.baseUnits, 0);
    const baseOrders = recs.reduce((s,r) => s + r.baseUnits, 0);

    const adjusted = recs.map(r => {
        const e = Math.abs(elast[r.category]?.value || 1);
        // Demand shift
        const newDemand = r.baseUnits * (1 + demandChange);
        // Competitor discount effect: if competitors discount more, we need deeper discounts
        let adjDiscount = r.discount + compChange * 100 * 0.3;
        // Inventory effect: more inventory → slightly deeper discount to clear
        adjDiscount += invChange * 100 * 0.15;
        adjDiscount = Math.max(0, Math.min(50, adjDiscount));
        const newPrice = Math.round(r.currentPrice * (1 - adjDiscount/100));
        const demandLift = 1 + (adjDiscount/100) * e;
        const newUnits = Math.round(newDemand * demandLift);
        const cost = state.data.products.find(p=>p.id===r.id)?.cost || r.currentPrice*0.6;
        return {
            ...r,
            adjDiscount: Math.round(adjDiscount*10)/10,
            adjNewPrice: newPrice,
            adjUnits: newUnits,
            adjRevenue: newPrice * newUnits,
            adjProfit: (newPrice - cost) * newUnits
        };
    });

    const totalRev = adjusted.reduce((s,r) => s+r.adjRevenue, 0);
    const totalProf = adjusted.reduce((s,r) => s+r.adjProfit, 0);
    const totalOrders = adjusted.reduce((s,r) => s+r.adjUnits, 0);
    const avgDiscount = adjusted.reduce((s,r) => s+r.adjDiscount, 0) / adjusted.length;

    animateValue('wi-revenue', 0, totalRev, 500, formatINR);
    animateValue('wi-profit', 0, totalProf, 500, formatINR);
    animateValue('wi-orders', 0, totalOrders, 500, formatUnits);
    animateValue('wi-discount', 0, avgDiscount, 500, v => v.toFixed(1)+'%');

    setWhatIfTrend('wi-revenue-trend', totalRev, baseRevenue);
    setWhatIfTrend('wi-profit-trend', totalProf, baseProfit);
    setWhatIfTrend('wi-orders-trend', totalOrders, baseOrders);
    const baseAvgDisc = recs.reduce((s,r) => s+r.discount,0)/recs.length;
    setWhatIfTrend('wi-discount-trend', avgDiscount, baseAvgDisc);

    // Update table
    const tbody = document.getElementById('whatif-table-body');
    tbody.innerHTML = adjusted.slice(0, 20).map(r => {
        const discCls = r.adjDiscount <= 10 ? 'low' : r.adjDiscount <= 25 ? 'medium' : 'high';
        return `
        <tr>
            <td class="fw-700">${r.name}</td>
            <td>${r.category}</td>
            <td>${formatINR(r.currentPrice)}</td>
            <td><span class="discount-badge ${discCls}">${r.adjDiscount.toFixed(1)}%</span></td>
            <td>${formatINR(r.adjNewPrice)}</td>
            <td>${formatINR(r.adjRevenue)}</td>
            <td class="${r.adjProfit > 0 ? 'text-success' : 'text-danger'}">${formatINR(r.adjProfit)}</td>
        </tr>`;
    }).join('');
}

function updateWhatIfKPIs() {
    // Render initial state (no changes)
    recalcWhatIf();
}

function setWhatIfTrend(elId, cur, base) {
    const el = document.getElementById(elId);
    if (!el) return;
    const pct = ((cur - base) / (base || 1)) * 100;
    const arrow = el.querySelector('.trend-arrow');
    const val = el.querySelector('.trend-val');
    if (pct > 0.5)       { el.className = 'kpi-trend up'; arrow.textContent = '↑'; }
    else if (pct < -0.5) { el.className = 'kpi-trend down'; arrow.textContent = '↓'; }
    else                 { el.className = 'kpi-trend flat'; arrow.textContent = '→'; }
    val.textContent = Math.abs(pct).toFixed(1) + '%';
}

function renderWhatIfTable() {
    // Initial render handled by recalcWhatIf()
}

// ─── Navigation ─────────────────────────────────────
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.dashboard-section');

    // Click navigation
    navItems.forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const sectionId = item.getAttribute('data-section');
            const target = document.getElementById(sectionId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            // Close mobile sidebar
            document.getElementById('sidebar').classList.remove('open');
        });
    });

    // Scroll spy
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navItems.forEach(n => n.classList.remove('active'));
                const active = document.querySelector(`.nav-item[data-section="${entry.target.id}"]`);
                if (active) active.classList.add('active');
            }
        });
    }, { rootMargin: '-20% 0px -60% 0px' });

    sections.forEach(s => observer.observe(s));

    // Mobile menu
    document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });
}

// ─── Search ─────────────────────────────────────────
function initSearch() {
    // Product search
    document.getElementById('product-search')?.addEventListener('input', debounce(e => {
        const q = e.target.value.toLowerCase();
        const prods = state.data.products.filter(p =>
            p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q)
        );
        renderProductTableRows(prods);
    }, 150));

    // Recommendations search
    document.getElementById('rec-search')?.addEventListener('input', debounce(e => {
        const q = e.target.value.toLowerCase();
        const recs = state.data.recommendations.filter(r =>
            r.name.toLowerCase().includes(q) || r.category.toLowerCase().includes(q)
        );
        renderRecTableRows(recs);
    }, 150));
}

// ─── Table Sorting ──────────────────────────────────
function initTableSort(tableId, data, renderFn) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const ths = table.querySelectorAll('th[data-sort]');
    ths.forEach(th => {
        th.addEventListener('click', () => {
            const key = th.getAttribute('data-sort');
            const prev = state.sortState[tableId];
            let dir = 'desc';
            if (prev && prev.key === key && prev.dir === 'desc') dir = 'asc';

            // Update visual
            ths.forEach(t => { t.classList.remove('sorted-asc','sorted-desc'); });
            th.classList.add(dir === 'asc' ? 'sorted-asc' : 'sorted-desc');

            state.sortState[tableId] = { key, dir };
            const sorted = [...data].sort((a,b) => {
                let va = a[key], vb = b[key];
                if (typeof va === 'string') va = va.toLowerCase();
                if (typeof vb === 'string') vb = vb.toLowerCase();
                if (va < vb) return dir === 'asc' ? -1 : 1;
                if (va > vb) return dir === 'asc' ? 1 : -1;
                return 0;
            });
            renderFn(sorted);
        });
    });
}

// ─── Utilities ──────────────────────────────────────
function truncate(s, len) { return s.length > len ? s.slice(0, len-1) + '…' : s; }

function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}
