'use strict';

const STORE_KEY = 'tally.v1';

const $list = document.getElementById('taskList');
const $empty = document.getElementById('empty');
const $tally = document.getElementById('tally');
const $remaining = document.getElementById('remaining');
const $date = document.getElementById('dayDate');
const $composer = document.getElementById('composer');
const $input = document.getElementById('taskInput');

let filter = 'all';
let state = load();

function todayKey() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function load() {
  let data = null;
  try { data = JSON.parse(localStorage.getItem(STORE_KEY)); } catch { /* corrupted store */ }
  if (!data || !Array.isArray(data.tasks)) data = { tasks: [], doneToday: null };
  if (!data.doneToday || data.doneToday.date !== todayKey()) {
    data.doneToday = { date: todayKey(), count: 0 };
  }
  return data;
}

function save() {
  localStorage.setItem(STORE_KEY, JSON.stringify(state));
}

/* strikes made today survive deleting the task — the tally records the work, not the row */
function bumpToday(delta) {
  if (state.doneToday.date !== todayKey()) state.doneToday = { date: todayKey(), count: 0 };
  state.doneToday.count = Math.max(0, state.doneToday.count + delta);
}

function newId() {
  return (crypto.randomUUID && crypto.randomUUID()) ||
    Date.now().toString(36) + Math.random().toString(36).slice(2);
}

/* ---- header ---- */

function renderHeader() {
  $date.textContent = new Date().toLocaleDateString(undefined, {
    weekday: 'long', month: 'long', day: 'numeric',
  });
  const left = state.tasks.filter(t => !t.done).length;
  $remaining.textContent =
    state.tasks.length === 0 ? 'A clean slate'
    : left === 0 ? 'All clear'
    : `${left} to go`;
  renderTally(state.doneToday.count);
}

function renderTally(count) {
  $tally.setAttribute('aria-label',
    count === 0 ? 'No tasks done yet today'
    : count === 1 ? '1 task done today'
    : `${count} tasks done today`);

  if (count === 0) {
    $tally.innerHTML = '<span class="day__tally-none">no strikes yet</span>';
    return;
  }

  const GW = 46, H = 30;
  const groups = Math.ceil(count / 5);
  const width = groups * GW;
  let marks = '';
  for (let g = 0; g < groups; g++) {
    const n = Math.min(5, count - g * 5);
    const x0 = g * GW;
    for (let i = 0; i < Math.min(n, 4); i++) {
      const x = x0 + 6 + i * 8;
      const tilt = (i % 2 === 0 ? 1 : -1) * 1.2;
      marks += `<line x1="${x - tilt}" y1="4" x2="${x + tilt}" y2="26" ` +
        'stroke="var(--cream)" stroke-width="2.5" stroke-linecap="round"/>';
    }
    if (n === 5) {
      marks += `<line x1="${x0}" y1="22" x2="${x0 + 36}" y2="7" ` +
        'stroke="var(--marigold)" stroke-width="2.5" stroke-linecap="round"/>';
    }
  }
  $tally.innerHTML =
    `<svg width="${width}" height="${H}" viewBox="0 0 ${width} ${H}" aria-hidden="true">${marks}</svg>`;
}

/* ---- list ---- */

function visible(task) {
  return filter === 'all' || (filter === 'active' ? !task.done : task.done);
}

function renderList() {
  $list.innerHTML = '';
  const shown = state.tasks.filter(visible);
  for (const t of shown) $list.appendChild(makeRow(t));
  $empty.hidden = shown.length !== 0;
  $empty.innerHTML = filter === 'done'
    ? 'Nothing struck through yet.'
    : 'Nothing on the list.<br>Add what’s next.';
}

function makeRow(task) {
  const li = document.createElement('li');
  li.className = 'task' + (task.done ? ' is-done' : '');
  li.dataset.id = task.id;

  const check = document.createElement('button');
  check.className = 'task__check';
  check.type = 'button';
  check.textContent = '✓';
  check.setAttribute('aria-pressed', String(task.done));
  check.setAttribute('aria-label', task.done ? 'Mark as not done' : 'Mark as done');
  check.addEventListener('click', () => toggleTask(task.id, li));

  const text = document.createElement('span');
  text.className = 'task__text';
  const inner = document.createElement('span');
  inner.className = 'task__text-inner';
  inner.textContent = task.text;
  text.appendChild(inner);

  const del = document.createElement('button');
  del.className = 'task__delete';
  del.type = 'button';
  del.textContent = '×';
  del.setAttribute('aria-label', `Delete “${task.text}”`);
  del.addEventListener('click', () => removeTask(task.id, li));

  li.append(check, text, del);
  attachSwipe(li, () => removeTask(task.id, li));
  return li;
}

/* ---- actions ---- */

function addTask(text) {
  const task = { id: newId(), text, done: false, createdAt: Date.now(), doneAt: null };
  state.tasks.unshift(task);
  save();
  renderHeader();
  if (visible(task)) {
    const row = makeRow(task);
    row.classList.add('is-entering');
    $list.prepend(row);
    $empty.hidden = true;
  }
}

function toggleTask(id, row) {
  const task = state.tasks.find(t => t.id === id);
  if (!task) return;
  task.done = !task.done;
  task.doneAt = task.done ? Date.now() : null;
  bumpToday(task.done ? 1 : -1);
  save();

  row.classList.toggle('is-done', task.done);
  const check = row.querySelector('.task__check');
  check.setAttribute('aria-pressed', String(task.done));
  check.setAttribute('aria-label', task.done ? 'Mark as not done' : 'Mark as done');
  renderHeader();

  /* let the strike finish before the row leaves a filtered view */
  if (!visible(task)) {
    setTimeout(() => {
      row.classList.add('is-leaving');
      setTimeout(renderList, 250);
    }, 450);
  }
}

function removeTask(id, row) {
  state.tasks = state.tasks.filter(t => t.id !== id);
  save();
  renderHeader();
  row.classList.add('is-leaving');
  setTimeout(renderList, 250);
}

/* ---- swipe left to delete (touch/pen; vertical scroll stays native) ---- */

function attachSwipe(el, onDelete) {
  let startX = 0, startY = 0, dx = 0, engaged = false, pid = null;

  el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse') return;
    startX = e.clientX;
    startY = e.clientY;
    dx = 0;
    engaged = false;
    pid = e.pointerId;
  });

  el.addEventListener('pointermove', e => {
    if (e.pointerId !== pid) return;
    const mx = e.clientX - startX;
    const my = e.clientY - startY;
    if (!engaged) {
      if (Math.abs(mx) > 12 && Math.abs(mx) > Math.abs(my) * 1.5) {
        engaged = true;
        el.setPointerCapture(pid);
        el.style.transition = 'none';
      } else {
        return;
      }
    }
    dx = Math.min(0, mx);
    el.style.transform = `translateX(${dx}px)`;
    el.style.opacity = String(Math.max(0.35, 1 + dx / 240));
  });

  const finish = e => {
    if (e.pointerId !== pid) return;
    const wasEngaged = engaged;
    engaged = false;
    pid = null;
    if (!wasEngaged) return;
    el.style.transition = '';
    if (dx < -80) {
      onDelete();
    } else {
      el.style.transform = '';
      el.style.opacity = '';
    }
  };
  el.addEventListener('pointerup', finish);
  el.addEventListener('pointercancel', finish);
}

/* ---- wiring ---- */

document.querySelectorAll('.chip').forEach(btn => {
  btn.addEventListener('click', () => {
    filter = btn.dataset.filter;
    document.querySelectorAll('.chip').forEach(b => {
      const on = b === btn;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-pressed', String(on));
    });
    renderList();
  });
});

$composer.addEventListener('submit', e => {
  e.preventDefault();
  const text = $input.value.trim();
  if (!text) return;
  addTask(text);
  $input.value = '';
  $input.focus();
});

renderHeader();
renderList();

if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  navigator.serviceWorker.register('sw.js').catch(() => { /* offline support is best-effort */ });
}
