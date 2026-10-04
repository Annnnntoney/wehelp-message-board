const form = document.querySelector('#message-form')
const formError = document.querySelector('#form-error')
const list = document.querySelector('#message-list')

function renderMessage(message) {
  const item = document.createElement('li')

  // 用 textContent 而不是 innerHTML：使用者輸入 <script> 也只會被當成文字（防 XSS）
  const text = document.createElement('p')
  text.textContent = message.content

  const image = document.createElement('img')
  image.src = message.imageUrl
  image.alt = message.content
  image.loading = 'lazy'

  item.append(text, image)
  return item
}

async function loadMessages() {
  const res = await fetch('/api/messages')
  const { data } = await res.json()
  list.replaceChildren(...data.map(renderMessage))
}

form.addEventListener('submit', async (event) => {
  event.preventDefault()
  const button = form.querySelector('button')
  button.disabled = true
  formError.textContent = ''

  try {
    const res = await fetch('/api/messages', { method: 'POST', body: new FormData(form) })
    const body = await res.json()
    if (!res.ok) {
      formError.textContent = body.message
      return
    }
    list.prepend(renderMessage(body.data))
    form.reset()
  } catch {
    formError.textContent = '連線失敗，請稍後再試'
  } finally {
    button.disabled = false
  }
})

loadMessages()
