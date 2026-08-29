export const shellApi = 1

function node(tag, className, text) {
  const element = document.createElement(tag)
  if (className) element.className = className
  if (text !== undefined) element.textContent = text
  return element
}

function decisionIdFromPath() {
  const match = window.location.pathname.match(/^\/panel\/decisions\/(\d+)$/)
  return match ? Number(match[1]) : null
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function humanize(value) {
  return value ? value.replaceAll('_', ' ') : 'waiting'
}

export function mount(el, ctx) {
  el.innerHTML = `
    <div class="dp-app">
      <header class="dp-hero">
        <div>
          <p class="dp-kicker">DURABLE DECISION REVIEW</p>
          <h1>Pressure-test the call.</h1>
          <p>Opportunity, risk, and execution argue independently. A moderator
            synthesizes. You decide.</p>
        </div>
        <button class="dp-new" type="button">New decision</button>
      </header>
      <main class="dp-layout">
        <aside class="dp-sidebar">
          <form class="dp-form" hidden>
            <label>Short name<input name="title" maxlength="120" required placeholder="Launch the pilot"></label>
            <label>Decision<textarea name="question" maxlength="500" required placeholder="Should we launch the pilot in September?"></textarea></label>
            <label>Context<textarea name="context" maxlength="4000" placeholder="Constraints, evidence, and what is already known"></textarea></label>
            <div class="dp-form-actions">
              <button class="dp-submit" type="submit">Convene panel</button>
              <button class="dp-cancel" type="button">Cancel</button>
            </div>
          </form>
          <div class="dp-list-head"><span>Decisions</span><span class="dp-count"></span></div>
          <div class="dp-list"></div>
        </aside>
        <section class="dp-detail"></section>
      </main>
      <div class="dp-error" role="alert" hidden></div>
    </div>
  `

  const form = el.querySelector('.dp-form')
  const list = el.querySelector('.dp-list')
  const count = el.querySelector('.dp-count')
  const detail = el.querySelector('.dp-detail')
  const error = el.querySelector('.dp-error')
  let decisions = []
  let selectedId = decisionIdFromPath()
  let pollTimer = null
  let disposed = false

  async function request(path, options = {}) {
    const response = await fetch(`${ctx.apiBase}${path}`, {
      ...options,
      headers: options.body ? { 'content-type': 'application/json' } : undefined,
    })
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || `Request failed (${response.status})`)
    }
    return response.status === 204 ? null : response.json()
  }

  function showError(message) {
    error.textContent = message
    error.hidden = !message
  }

  function setPath(id) {
    selectedId = id
    ctx.navigate(id ? `/panel/decisions/${id}` : '/panel')
  }

  function statusBadge(status) {
    const badge = node('span', `dp-status dp-status-${status.state}`)
    badge.textContent = status.gate === 'record_decision' ? 'needs your call' : humanize(status.state)
    return badge
  }

  function renderList() {
    list.replaceChildren()
    count.textContent = String(decisions.length)
    for (const decision of decisions) {
      const button = node('button', 'dp-list-item')
      button.type = 'button'
      if (decision.id === String(selectedId)) button.classList.add('is-active')
      const top = node('span', 'dp-list-top')
      top.append(node('strong', '', decision.title), statusBadge(decision.status))
      button.append(top, node('span', 'dp-list-question', decision.question))
      button.addEventListener('click', () => {
        setPath(Number(decision.id))
        renderList()
        loadDetail()
      })
      list.append(button)
    }
    if (!decisions.length) {
      list.append(node('p', 'dp-empty-small', 'No decisions yet. Convene the first panel.'))
    }
  }

  function renderAssessment(assessment) {
    const card = node('article', `dp-advisor dp-${assessment.perspective}`)
    const header = node('div', 'dp-advisor-head')
    header.append(
      node('span', 'dp-advisor-name', assessment.perspective),
      node('span', 'dp-confidence', `${assessment.confidence}% confidence`),
    )
    const position = node('span', 'dp-position', humanize(assessment.position))
    const reasons = node('ul', 'dp-points')
    for (const item of assessment.rationale) reasons.append(node('li', '', item))
    const unknowns = node('ul', 'dp-unknowns')
    for (const item of assessment.uncertainties) unknowns.append(node('li', '', item))
    card.append(
      header,
      position,
      node('h3', '', assessment.headline),
      reasons,
      node('p', 'dp-mini-label', 'UNCERTAINTIES'),
      unknowns,
    )
    return card
  }

  function bulletSection(title, items) {
    const section = node('section', 'dp-synthesis-section')
    section.append(node('h3', '', title))
    const values = node('ul')
    for (const item of items) values.append(node('li', '', item))
    section.append(values)
    return section
  }

  function outcomeControls(decision) {
    const wrap = node('section', 'dp-outcome')
    wrap.append(
      node('p', 'dp-kicker', 'THE HUMAN CALL'),
      node('h2', '', 'What do you decide?'),
      node('p', '', 'The panel advises. The outcome remains yours.'),
    )
    const note = document.createElement('textarea')
    note.placeholder = 'Decision note (optional)'
    note.maxLength = 2000
    wrap.append(note)
    const actions = node('div', 'dp-outcome-actions')
    for (const action of ['proceed', 'revise', 'pass']) {
      const button = node('button', `dp-action dp-action-${action}`, action)
      button.type = 'button'
      button.addEventListener('click', async () => {
        for (const item of actions.querySelectorAll('button')) item.disabled = true
        showError('')
        try {
          await request(`/decisions/${decision.id}/outcome`, {
            method: 'POST',
            body: JSON.stringify({ action, note: note.value }),
          })
          await refresh()
        } catch (cause) {
          showError(cause.message)
          for (const item of actions.querySelectorAll('button')) item.disabled = false
        }
      })
      actions.append(button)
    }
    wrap.append(actions)
    return wrap
  }

  function renderDetail(decision) {
    detail.replaceChildren()
    if (!decision) {
      detail.append(
        node('p', 'dp-kicker', 'YOUR NEXT CALL'),
        node('h2', 'dp-empty-title', 'A consequential question belongs here.'),
        node('p', 'dp-empty-copy', 'Give the panel enough context to disagree usefully.'),
      )
      return
    }

    const heading = node('header', 'dp-decision-head')
    const meta = node('div', 'dp-decision-meta')
    meta.append(statusBadge(decision.status), node('span', '', formatDate(decision.createdAt)))
    heading.append(
      meta,
      node('h2', '', decision.title),
      node('p', 'dp-question', decision.question),
    )
    if (decision.context) heading.append(node('p', 'dp-context', decision.context))
    detail.append(heading)

    if (!decision.assessments.length) {
      const waiting = node('section', 'dp-waiting')
      waiting.append(
        node('span', 'dp-pulse'),
        node('h3', '', 'The panel is deliberating'),
        node('p', '', 'Completed agent calls are durable. This page will update as the views arrive.'),
      )
      detail.append(waiting)
      return
    }

    const grid = node('section', 'dp-advisor-grid')
    for (const assessment of decision.assessments) grid.append(renderAssessment(assessment))
    detail.append(grid)

    if (decision.synthesis) {
      const synthesis = node('section', 'dp-synthesis')
      const top = node('div', 'dp-synthesis-top')
      top.append(
        node('div', 'dp-avatar', 'M'),
        node('div', '', ''),
      )
      top.lastChild.append(
        node('p', 'dp-kicker', 'MODERATOR'),
        node('h2', '', `Recommendation: ${decision.synthesis.recommendation}`),
      )
      synthesis.append(top, node('p', 'dp-summary', decision.synthesis.summary))
      const columns = node('div', 'dp-synthesis-grid')
      columns.append(
        bulletSection('Common ground', decision.synthesis.common_ground),
        bulletSection('Tradeoffs', decision.synthesis.tradeoffs),
        bulletSection('Questions to resolve', decision.synthesis.questions_to_resolve),
      )
      synthesis.append(columns)
      const next = node('p', 'dp-next-step')
      next.append(node('span', '', 'NEXT STEP'), document.createTextNode(decision.synthesis.next_step))
      synthesis.append(next)
      detail.append(synthesis)
    }

    if (decision.outcome) {
      const outcome = node('section', `dp-final dp-final-${decision.outcome}`)
      outcome.append(
        node('p', 'dp-kicker', 'DECIDED'),
        node('h2', '', humanize(decision.outcome)),
        node('p', '', decision.outcomeNote || 'No decision note was recorded.'),
        node('time', '', formatDate(decision.decidedAt)),
      )
      detail.append(outcome)
    } else if (decision.status.state === 'parked' && decision.status.gate === 'record_decision') {
      detail.append(outcomeControls(decision))
    }
  }

  async function loadDetail() {
    if (!selectedId) {
      renderDetail(null)
      return
    }
    try {
      const decision = await request(`/decisions/${selectedId}`)
      renderDetail(decision)
      schedulePoll(decision.status.state)
    } catch (cause) {
      showError(cause.message)
    }
  }

  function schedulePoll(state) {
    window.clearTimeout(pollTimer)
    if (!disposed && ['scheduled', 'running'].includes(state)) {
      pollTimer = window.setTimeout(refresh, 4000)
    }
  }

  async function refresh() {
    showError('')
    try {
      decisions = await request('/decisions')
      if (!selectedId && decisions.length) {
        selectedId = Number(decisions[0].id)
      }
      renderList()
      await loadDetail()
    } catch (cause) {
      showError(cause.message)
    }
  }

  el.querySelector('.dp-new').addEventListener('click', () => {
    form.hidden = false
    form.querySelector('input').focus()
  })
  el.querySelector('.dp-cancel').addEventListener('click', () => {
    form.reset()
    form.hidden = true
  })
  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    showError('')
    const submit = form.querySelector('.dp-submit')
    submit.disabled = true
    const values = new FormData(form)
    try {
      const created = await request('/decisions', {
        method: 'POST',
        body: JSON.stringify({
          title: values.get('title'),
          question: values.get('question'),
          context: values.get('context'),
        }),
      })
      form.reset()
      form.hidden = true
      setPath(created.id)
      await refresh()
    } catch (cause) {
      showError(cause.message)
    } finally {
      submit.disabled = false
    }
  })

  const onPopState = () => {
    selectedId = decisionIdFromPath()
    renderList()
    loadDetail()
  }
  window.addEventListener('popstate', onPopState)
  refresh()

  return () => {
    disposed = true
    window.clearTimeout(pollTimer)
    window.removeEventListener('popstate', onPopState)
    el.replaceChildren()
  }
}
