/**
 * Sandbox Inspect Mode Library
 *
 * This script is injected into iframe pages to enable element inspection.
 * It communicates with the parent window via postMessage.
 *
 * Usage: Include this script in your iframe page
 * <script src="/sandbox_inspect.js"></script>
 */

;(function () {
  'use strict'

  // Prevent multiple initializations
  if (window.__SANDBOX_INSPECT_INITIALIZED__) {
    return
  }
  window.__SANDBOX_INSPECT_INITIALIZED__ = true

  // ============================================
  // Configuration
  // ============================================
  const CONFIG = {
    MESSAGE_PREFIX: 'sandbox-inspect',
    EXCLUDED_TAGS: [
      'html',
      'body',
      'head',
      'script',
      'style',
      'meta',
      'link',
      'title',
    ],
    THROTTLE_DELAY: 16, // ~60fps
  }

  // ============================================
  // State Management
  // ============================================
  const state = {
    enabled: false,
    editMode: false, // Edit mode state
    hoveredElement: null,
    selectedElement: null,
    parentOrigin: '*', // Will be set when receiving first message from parent
    // Drag state
    isDragging: false,
    dragElement: null,
    dragStartX: 0,
    dragStartY: 0,
    dragOffsetX: 0,
    dragOffsetY: 0,
    dropTarget: null,
    dropPosition: null, // 'before', 'after', 'inside'
  }

  // ============================================
  // Edit Mode Configuration
  // ============================================
  const editModeConfig = {
    debounceDelay: 5000, // 5 seconds to merge edits
    minDebounceDelay: 500, // Minimum delay before saving (for rapid typing)
  }

  const editModeState = {
    pendingSnapshot: null, // Snapshot captured before current edit batch
    debounceTimer: null, // Timer for debounced save
    lastEditTime: 0, // Timestamp of last edit
    editCount: 0, // Number of edits in current batch
    isEditing: false, // Currently in an edit batch
  }

  // ============================================
  // History Management
  // ============================================
  const historyConfig = {
    maxHistorySize: 50,
  }

  const historyState = {
    history: [], // Array of snapshots
    currentIndex: -1, // Current position in history
    isRestoring: false, // Flag to prevent capturing during restore
  }

  /**
   * Capture current DOM state as a snapshot
   * @param {string} operationType - Type of operation that triggered the snapshot
   * @param {string} description - Human-readable description
   * @returns {Object} Snapshot object
   */
  function captureSnapshot(operationType = 'manual', description = '') {
    if (historyState.isRestoring) return null

    try {
      const bodyClone = document.body.cloneNode(true)

      // Remove inspector-added elements from the snapshot
      const inspectorElements = bodyClone.querySelectorAll(
        '.__sandbox-drag-ghost__, .__sandbox-drop-indicator__, #__sandbox-edit-mode-styles__'
      )
      inspectorElements.forEach(el => el.remove())

      // Remove contenteditable attribute from the clone (it's a mode state, not content)
      bodyClone.removeAttribute('contenteditable')

      const snapshot = {
        id: `snapshot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        htmlContent: bodyClone.innerHTML,
        operationType: operationType,
        description: description || `${operationType} operation`,
        scrollX: window.scrollX || 0,
        scrollY: window.scrollY || 0,
      }

      return snapshot
    } catch (error) {
      console.error('[SandboxInspect] Failed to capture snapshot:', error)
      return null
    }
  }

  /**
   * Add a snapshot to history
   * @param {Object} snapshot - Snapshot to add
   */
  function addSnapshotToHistory(snapshot) {
    if (!snapshot || historyState.isRestoring) return

    // If we're not at the end of history, truncate future states
    if (historyState.currentIndex < historyState.history.length - 1) {
      historyState.history = historyState.history.slice(
        0,
        historyState.currentIndex + 1
      )
    }

    // Compute diff with previous snapshot using diff-dom
    if (historyState.history.length > 0) {
      const prevSnapshot = historyState.history[historyState.history.length - 1]
      snapshot.diff = computeDomDiff(
        prevSnapshot.htmlContent,
        snapshot.htmlContent
      )
    } else {
      snapshot.diff = []
    }

    // Add new snapshot
    historyState.history.push(snapshot)
    historyState.currentIndex = historyState.history.length - 1

    // Limit history size
    if (historyState.history.length > historyConfig.maxHistorySize) {
      const removeCount =
        historyState.history.length - historyConfig.maxHistorySize
      historyState.history.splice(0, removeCount)
      historyState.currentIndex -= removeCount
    }

    // Notify parent of history state change
    sendHistoryState()

    console.log(
      '[SandboxInspect] Snapshot added:',
      snapshot.operationType,
      `(${historyState.currentIndex + 1}/${historyState.history.length})`
    )
  }

  /**
   * Capture and add a snapshot to history
   * @param {string} operationType - Type of operation
   * @param {string} description - Description
   */
  function saveToHistory(operationType, description) {
    const snapshot = captureSnapshot(operationType, description)
    if (snapshot) {
      addSnapshotToHistory(snapshot)
    }
  }

  /**
   * Apply a snapshot to restore DOM state
   * @param {Object} snapshot - Snapshot to apply
   * @returns {boolean} Success status
   */
  function applySnapshot(snapshot) {
    if (!snapshot) return false

    historyState.isRestoring = true

    // Remember edit mode state before restoring
    const wasInEditMode = state.editMode

    // If in edit mode, temporarily teardown observer to avoid triggering during restore
    if (wasInEditMode && editModeObserver) {
      editModeObserver.disconnect()
    }

    try {
      // Restore HTML content
      document.body.innerHTML = snapshot.htmlContent

      // Restore scroll position
      window.scrollTo(snapshot.scrollX || 0, snapshot.scrollY || 0)

      // Clear selected element since DOM has changed
      state.selectedElement = null
      state.hoveredElement = null

      // Notify parent about cleared selection
      sendToParent('unselect', { element: null, reason: 'historyRestore' })
      sendToParent('unhover', { element: null, reason: 'historyRestore' })

      // If we were in edit mode, restore contentEditable and styles
      if (wasInEditMode) {
        document.body.contentEditable = 'true'
        // Re-add edit mode styles (they were removed from snapshot)
        addEditModeStyles()
        // Reset edit state since we just restored
        editModeState.isEditing = false
        editModeState.pendingSnapshot = null
        editModeState.editCount = 0
        if (editModeState.debounceTimer) {
          clearTimeout(editModeState.debounceTimer)
          editModeState.debounceTimer = null
        }
        // Notify parent that pending edits were cleared
        sendToParent('editActivity', {
          editCount: 0,
          pending: false,
        })
      }

      console.log('[SandboxInspect] Snapshot applied:', snapshot.operationType)
      return true
    } catch (error) {
      console.error('[SandboxInspect] Failed to apply snapshot:', error)
      return false
    } finally {
      historyState.isRestoring = false
      // Always reconnect observer if we were in edit mode, even if an error occurred
      if (wasInEditMode && editModeObserver) {
        editModeObserver.observe(document.body, {
          childList: true,
          subtree: true,
          attributes: true,
          characterData: true,
          characterDataOldValue: true,
        })
      }
    }
  }

  /**
   * Undo - go back in history
   * @returns {boolean} Success status
   */
  function undo() {
    // If in edit mode with pending changes, flush them first
    if (state.editMode && editModeState.isEditing) {
      flushEditHistory()
    }

    if (!canUndo()) {
      console.log('[SandboxInspect] Cannot undo - at beginning of history')
      return false
    }

    // Get the snapshot being undone (current snapshot) - its diff shows what will be reverted
    const undoneSnapshot = historyState.history[historyState.currentIndex]
    const targetIndex = historyState.currentIndex - 1
    const targetSnapshot = historyState.history[targetIndex]

    if (applySnapshot(targetSnapshot)) {
      historyState.currentIndex = targetIndex
      sendHistoryState()
      // Send the undone snapshot's info so the diff shows what was actually undone
      sendToParent('historyUndo', {
        snapshot: getSnapshotInfo(undoneSnapshot),
        historyInfo: getHistoryInfo(),
      })
      return true
    }
    return false
  }

  /**
   * Redo - go forward in history
   * @returns {boolean} Success status
   */
  function redo() {
    // If in edit mode with pending changes, flush them first
    if (state.editMode && editModeState.isEditing) {
      flushEditHistory()
    }

    if (!canRedo()) {
      console.log('[SandboxInspect] Cannot redo - at end of history')
      return false
    }

    const targetIndex = historyState.currentIndex + 1
    const targetSnapshot = historyState.history[targetIndex]

    if (applySnapshot(targetSnapshot)) {
      historyState.currentIndex = targetIndex
      sendHistoryState()
      sendToParent('historyRedo', {
        snapshot: getSnapshotInfo(targetSnapshot),
        historyInfo: getHistoryInfo(),
      })
      return true
    }
    return false
  }

  /**
   * Check if undo is possible
   * @returns {boolean}
   */
  function canUndo() {
    return historyState.currentIndex > 0
  }

  /**
   * Check if redo is possible
   * @returns {boolean}
   */
  function canRedo() {
    return historyState.currentIndex < historyState.history.length - 1
  }

  /**
   * Get history information
   * @returns {Object} History info
   */
  function getHistoryInfo() {
    return {
      historySize: historyState.history.length,
      currentIndex: historyState.currentIndex,
      canUndo: canUndo(),
      canRedo: canRedo(),
    }
  }

  // diff-dom loading state
  let diffDomLoaded = false
  let diffDomLoading = false
  let diffDomLoadCallbacks = []

  /**
   * Load diff-dom library from CDN
   * @returns {Promise<boolean>} Whether loading was successful
   */
  function loadDiffDom() {
    return new Promise(resolve => {
      if (diffDomLoaded && window.diffDOM) {
        resolve(true)
        return
      }

      if (diffDomLoading) {
        diffDomLoadCallbacks.push(resolve)
        return
      }

      diffDomLoading = true

      const script = document.createElement('script')
      // Use the browser build which exposes window.diffDOM global
      script.src =
        'https://cdn.jsdelivr.net/npm/diff-dom@5.2.1/browser/diffDOM.js'

      script.onload = () => {
        diffDomLoaded = true
        diffDomLoading = false
        console.log('[SandboxInspect] diff-dom loaded successfully')
        resolve(true)
        diffDomLoadCallbacks.forEach(cb => cb(true))
        diffDomLoadCallbacks = []
      }

      script.onerror = () => {
        diffDomLoading = false
        console.error('[SandboxInspect] Failed to load diff-dom')
        resolve(false)
        diffDomLoadCallbacks.forEach(cb => cb(false))
        diffDomLoadCallbacks = []
      }

      document.head.appendChild(script)
    })
  }

  /**
   * Convert a route array to CSS path by traversing the DOM
   * diff-dom uses childNodes indices (includes text nodes), not children indices
   * @param {Element} container - The container element to traverse from
   * @param {Array<number>} route - Array of childNodes indices representing the path
   * @returns {string|null} CSS selector path from body
   */
  function routeToCssPath(container, route) {
    if (!container || !route || route.length === 0) {
      return null
    }

    try {
      let current = container
      const pathParts = []

      for (const index of route) {
        // diff-dom uses childNodes (includes text nodes), not children
        if (!current.childNodes || index >= current.childNodes.length) {
          // Route is invalid or element doesn't exist
          return null
        }

        const node = current.childNodes[index]

        // Skip non-element nodes (text nodes, comments, etc.)
        if (node.nodeType !== 1) {
          // If it's a text node, we can't build a CSS path to it
          // Return path to parent with a note
          if (pathParts.length > 0) {
            return pathParts.join(' > ') + ' > [text]'
          }
          return '[text]'
        }

        current = node

        // Build selector for this element
        let selector = current.tagName.toLowerCase()

        // Add id if available (makes it unique)
        if (current.id) {
          selector = `#${CSS.escape(current.id)}`
          pathParts.length = 0 // Clear previous parts, id is unique
          pathParts.push(selector)
          continue
        }

        // Add classes (limited to 3)
        if (current.className && typeof current.className === 'string') {
          const classes = current.className
            .split(/\s+/)
            .filter(c => c && !c.startsWith('__'))
            .slice(0, 3)
          if (classes.length > 0) {
            selector += '.' + classes.map(c => CSS.escape(c)).join('.')
          }
        }

        // Add nth-child for uniqueness (based on element siblings only)
        if (current.parentNode) {
          const siblings = current.parentNode.children
          const nthChild = Array.from(siblings).indexOf(current) + 1
          if (nthChild > 0) {
            selector += `:nth-child(${nthChild})`
          }
        }

        pathParts.push(selector)
      }

      return pathParts.length > 0 ? pathParts.join(' > ') : null
    } catch (e) {
      console.error('[SandboxInspect] routeToCssPath failed:', e)
      return null
    }
  }

  /**
   * Compute DOM diff between two HTML strings using diff-dom library
   * Returns diff-dom result array with added cssPath for each diff item
   * @param {string} oldHtml - Previous HTML content
   * @param {string} newHtml - New HTML content
   * @returns {Array} Diff-dom result array with cssPath added
   */
  function computeDomDiff(oldHtml, newHtml) {
    if (!oldHtml || !newHtml) {
      return []
    }

    if (oldHtml === newHtml) {
      return []
    }

    // Use diff-dom library if available
    if (window.diffDOM && window.diffDOM.DiffDOM) {
      try {
        const dd = new window.diffDOM.DiffDOM()

        // Create temporary elements to parse HTML
        const oldContainer = document.createElement('div')
        const newContainer = document.createElement('div')
        oldContainer.innerHTML = oldHtml
        newContainer.innerHTML = newHtml

        // Compute diff
        const diff = dd.diff(oldContainer, newContainer)

        if (!diff || diff.length === 0) {
          return []
        }

        // Add cssPath to each diff item
        const enhancedDiff = diff.map(item => {
          const enhanced = { ...item }

          // Convert route to cssPath
          // For most actions, route points to the target element in the old DOM
          // For 'addElement', route points to the parent, and the new element is at position
          if (item.route && Array.isArray(item.route)) {
            // Use oldContainer for most operations, newContainer for addElement
            const container =
              item.action === 'addElement' ? newContainer : oldContainer
            enhanced.cssPath = routeToCssPath(container, item.route)
          }

          return enhanced
        })

        return enhancedDiff
      } catch (e) {
        console.error('[SandboxInspect] diff-dom failed:', e)
        return []
      }
    }

    // Fallback: return empty array when diff-dom is not loaded
    return []
  }

  /**
   * Get snapshot info (without full HTML content)
   * @param {Object} snapshot - Snapshot
   * @returns {Object} Snapshot info
   */
  function getSnapshotInfo(snapshot) {
    if (!snapshot) return null
    return {
      id: snapshot.id,
      timestamp: snapshot.timestamp,
      operationType: snapshot.operationType,
      description: snapshot.description,
      diff: snapshot.diff || null,
    }
  }

  /**
   * Send history state to parent
   */
  function sendHistoryState() {
    sendToParent('historyState', getHistoryInfo())
  }

  /**
   * Clear history
   */
  function clearHistory() {
    historyState.history = []
    historyState.currentIndex = -1
    sendHistoryState()
    console.log('[SandboxInspect] History cleared')
  }

  /**
   * Get diff between initial state and current state using diff-dom
   */
  function getDiffFromInitial() {
    // Determine the initial snapshot to use for comparison
    let initialSnapshot = null

    // First, try to use the first history entry
    if (historyState.history.length >= 1) {
      initialSnapshot = historyState.history[0]
    }
    // If no history but we're in edit mode with a pending snapshot, use that as reference
    else if (state.editMode && editModeState.pendingSnapshot) {
      initialSnapshot = editModeState.pendingSnapshot
    }

    if (!initialSnapshot) {
      sendToParent('diffFromInitial', {
        diff: null,
        error: 'No initial state available',
      })
      return
    }

    const currentSnapshot = captureSnapshot('current', 'Current state')

    if (!currentSnapshot) {
      sendToParent('diffFromInitial', {
        diff: null,
        error: 'Failed to capture current state',
      })
      return
    }

    // Use diff-dom for DOM-level diff
    const diff = computeDomDiff(
      initialSnapshot.htmlContent,
      currentSnapshot.htmlContent
    )

    sendToParent('diffFromInitial', {
      diff: diff,
      initialSnapshot: getSnapshotInfo(initialSnapshot),
      historyInfo: getHistoryInfo(),
      hasPendingEdits: editModeState.isEditing,
    })
  }

  /**
   * Capture initial state
   */
  function captureInitialState() {
    if (historyState.history.length === 0) {
      saveToHistory('initial', 'Initial state')
    }
  }

  // ============================================
  // Utility Functions
  // ============================================

  /**
   * Simple throttle function
   */
  function throttle(func, delay) {
    let lastCall = 0
    let timeoutId = null

    const throttled = function (...args) {
      const now = Date.now()
      const remaining = delay - (now - lastCall)

      if (remaining <= 0) {
        if (timeoutId) {
          clearTimeout(timeoutId)
          timeoutId = null
        }
        lastCall = now
        func.apply(this, args)
      } else if (!timeoutId) {
        timeoutId = setTimeout(() => {
          lastCall = Date.now()
          timeoutId = null
          func.apply(this, args)
        }, remaining)
      }
    }

    throttled.cancel = function () {
      if (timeoutId) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
    }

    return throttled
  }

  /**
   * Check if element should be excluded from inspection
   */
  function isExcludedElement(element) {
    if (!element || element.nodeType !== 1) return true
    const tagName = element.tagName.toLowerCase()
    return CONFIG.EXCLUDED_TAGS.includes(tagName)
  }

  /**
   * Get element's bounding rect relative to viewport
   */
  function getElementRect(element) {
    if (!element) return null

    const rect = element.getBoundingClientRect()
    return {
      x: rect.left,
      y: rect.top,
      width: rect.width,
      height: rect.height,
      right: rect.right,
      bottom: rect.bottom,
    }
  }

  /**
   * Get detailed CSS path for an element
   */
  function getCssPath(element, options = {}) {
    const defaults = {
      useIds: true,
      useClasses: true,
      useNthChild: true,
      maxClasses: 3,
    }
    const settings = { ...defaults, ...options }

    if (!element || element.nodeType !== 1) return null

    const path = []
    let current = element

    while (current && current.nodeType === 1) {
      let selector = current.tagName.toLowerCase()

      // Use ID if available
      if (settings.useIds && current.id) {
        selector = `#${CSS.escape(current.id)}`
        path.unshift(selector)
        break
      }

      // Add classes
      if (
        settings.useClasses &&
        current.className &&
        typeof current.className === 'string'
      ) {
        const classes = current.className
          .split(/\s+/)
          .filter(c => c && !c.startsWith('__'))
          .slice(0, settings.maxClasses)

        if (classes.length > 0) {
          selector += '.' + classes.map(c => CSS.escape(c)).join('.')
        }
      }

      // Add nth-child for uniqueness
      if (settings.useNthChild && current.parentNode) {
        const index =
          Array.from(current.parentNode.children).indexOf(current) + 1
        selector += `:nth-child(${index})`
      }

      path.unshift(selector)
      current = current.parentNode

      // Stop at body
      if (
        current &&
        current.tagName &&
        current.tagName.toLowerCase() === 'body'
      ) {
        break
      }
    }

    return path.join(' > ')
  }

  /**
   * Get element info for sending to parent
   * Note: All returned data must be JSON-serializable (no DOM objects)
   */
  function getElementInfo(element) {
    if (!element) return null

    const rect = getElementRect(element)
    if (!rect) return null

    // Ensure className is a string (SVG elements have SVGAnimatedString)
    let className = element.className
    if (className && typeof className !== 'string') {
      className = className.baseVal || String(className)
    }

    return {
      tagName: element.tagName.toLowerCase(),
      id: element.id || null,
      className: className || null,
      rect: rect,
      cssPath: getCssPath(element),
      textContent: element.textContent
        ? element.textContent.slice(0, 100).trim()
        : null,
      attributes: getElementAttributes(element),
      outerHTML: null, // Will be populated only for select events
    }
  }

  /**
   * Get key attributes of an element
   */
  function getElementAttributes(element) {
    const attrs = {}
    const importantAttrs = [
      'href',
      'src',
      'alt',
      'title',
      'type',
      'name',
      'value',
      'placeholder',
    ]

    for (const attr of importantAttrs) {
      if (element.hasAttribute(attr)) {
        attrs[attr] = element.getAttribute(attr)
      }
    }

    return attrs
  }

  /**
   * Find meaningful parent element (for Alt+Click)
   */
  function findMeaningfulParent(element) {
    if (!element || !element.parentElement) return null

    const tagName = element.tagName.toLowerCase()

    // Table elements -> select table
    if (['td', 'th', 'tr', 'tbody', 'thead', 'tfoot'].includes(tagName)) {
      const table = element.closest('table')
      if (table) return table
    }

    // List items -> select list
    if (tagName === 'li') {
      const list = element.closest('ul, ol')
      if (list) return list
    }

    // Find nearest block container
    const blockTags = [
      'div',
      'section',
      'article',
      'aside',
      'header',
      'footer',
      'main',
      'figure',
      'blockquote',
      'table',
      'ul',
      'ol',
      'form',
      'nav',
    ]

    let parent = element.parentElement
    while (parent && parent !== document.body) {
      if (blockTags.includes(parent.tagName.toLowerCase())) {
        return parent
      }
      parent = parent.parentElement
    }

    return null
  }

  // ============================================
  // PostMessage Communication
  // ============================================

  /**
   * Send message to parent window
   */
  function sendToParent(type, data = {}) {
    if (!window.parent || window.parent === window) return

    const message = {
      source: CONFIG.MESSAGE_PREFIX,
      type: type,
      data: data,
      timestamp: Date.now(),
    }

    try {
      window.parent.postMessage(message, state.parentOrigin)
    } catch (e) {
      console.error('[SandboxInspect] Failed to send message to parent:', e)
    }
  }

  /**
   * Handle messages from parent window
   */
  function handleParentMessage(event) {
    const message = event.data

    // Validate message format
    if (!message || message.source !== CONFIG.MESSAGE_PREFIX) return

    // Store parent origin for security
    if (state.parentOrigin === '*' && event.origin) {
      state.parentOrigin = event.origin
    }

    switch (message.type) {
      case 'enable':
        enableInspectMode()
        break
      case 'disable':
        disableInspectMode()
        break
      case 'clear':
        clearAllStates()
        break
      case 'getState':
        sendCurrentState()
        break
      case 'ping':
        sendToParent('pong', {
          ready: true,
          url: window.location.href,
          title: document.title,
          historyInfo: getHistoryInfo(),
        })
        break
      // History commands
      case 'undo':
        undo()
        break
      case 'redo':
        redo()
        break
      case 'getHistoryState':
        sendHistoryState()
        break
      case 'clearHistory':
        clearHistory()
        break
      case 'getDiffFromInitial':
        getDiffFromInitial()
        break
      // Edit mode commands
      case 'enableEditMode':
        enableEditMode()
        break
      case 'disableEditMode':
        disableEditMode()
        break
      case 'flushEditHistory':
        flushEditHistory()
        break
      default:
        console.warn('[SandboxInspect] Unknown message type:', message.type)
    }
  }

  /**
   * Send current state to parent
   */
  function sendCurrentState() {
    sendToParent('state', {
      enabled: state.enabled,
      hoveredElement: getElementInfo(state.hoveredElement),
      selectedElement: getElementInfo(state.selectedElement),
    })
  }

  // ============================================
  // Event Handlers
  // ============================================

  /**
   * Handle mouse over event
   */
  function handleMouseOver(event) {
    if (!state.enabled) return

    const element = event.target
    if (isExcludedElement(element)) return

    // Don't update if same element
    if (state.hoveredElement === element) return

    state.hoveredElement = element

    sendToParent('hover', {
      element: getElementInfo(element),
    })

    event.stopPropagation()
  }

  /**
   * Handle mouse out event
   */
  function handleMouseOut(event) {
    if (!state.enabled) return

    const element = event.target
    if (isExcludedElement(element)) return

    // Only clear if leaving the hovered element
    if (state.hoveredElement === element) {
      state.hoveredElement = null

      sendToParent('unhover', {
        element: null,
      })
    }

    event.stopPropagation()
  }

  /**
   * Handle click event
   */
  function handleClick(event) {
    if (!state.enabled) return

    // Prevent default click behavior (links, buttons, etc.)
    event.preventDefault()
    event.stopPropagation()

    let element = event.target
    if (isExcludedElement(element)) return

    // Alt+Click: select parent container
    if (event.altKey) {
      const parent = findMeaningfulParent(element)
      if (parent) {
        element = parent
      }
    }

    // Toggle selection if clicking same element
    if (state.selectedElement === element) {
      state.selectedElement = null
      sendToParent('unselect', {
        element: null,
      })
    } else {
      state.selectedElement = element
      const elementInfo = getElementInfo(element)
      // Add outerHTML for select events only, limited to 1000 characters
      if (elementInfo && element.outerHTML) {
        const html = element.outerHTML
        elementInfo.outerHTML =
          html.length > 1000 ? html.slice(0, 1000) + '...' : html
      }
      sendToParent('select', {
        element: elementInfo,
      })
    }
  }

  /**
   * Handle mousedown event for drag initiation
   */
  function handleMouseDown(event) {
    if (!state.enabled || !state.selectedElement) return

    // Only start drag if clicking on the selected element
    if (
      !state.selectedElement.contains(event.target) &&
      state.selectedElement !== event.target
    ) {
      return
    }

    // Shift+Click to start dragging
    if (!event.shiftKey) return

    event.preventDefault()
    event.stopPropagation()

    state.isDragging = true
    state.dragElement = state.selectedElement
    state.dragStartX = event.clientX
    state.dragStartY = event.clientY

    const rect = state.dragElement.getBoundingClientRect()
    state.dragOffsetX = event.clientX - rect.left
    state.dragOffsetY = event.clientY - rect.top

    // Add dragging visual style
    state.dragElement.style.opacity = '0.5'
    state.dragElement.style.pointerEvents = 'none'
    document.body.style.cursor = 'grabbing'

    // Create drag ghost element
    createDragGhost(state.dragElement, event.clientX, event.clientY)

    sendToParent('dragStart', {
      element: getElementInfo(state.dragElement),
      startX: event.clientX,
      startY: event.clientY,
    })

    console.log('[SandboxInspect] Drag started')
  }

  /**
   * Handle mousemove event for dragging
   */
  function handleDragMove(event) {
    if (!state.isDragging || !state.dragElement) return

    event.preventDefault()
    event.stopPropagation()

    // Update ghost position
    updateDragGhost(event.clientX, event.clientY)

    // Find drop target
    const elementsAtPoint = document.elementsFromPoint(
      event.clientX,
      event.clientY
    )
    let dropTarget = null
    let dropPosition = null

    for (const elem of elementsAtPoint) {
      // Skip the drag element, ghost, and excluded elements
      if (
        elem === state.dragElement ||
        elem.classList.contains('__sandbox-drag-ghost__') ||
        elem.classList.contains('__sandbox-drop-indicator__') ||
        isExcludedElement(elem) ||
        state.dragElement.contains(elem)
      ) {
        continue
      }
      dropTarget = elem
      break
    }

    if (dropTarget) {
      const targetRect = dropTarget.getBoundingClientRect()
      const relativeY = event.clientY - targetRect.top
      const targetHeight = targetRect.height

      // Determine drop position based on mouse position within target
      if (relativeY < targetHeight * 0.25) {
        dropPosition = 'before'
      } else if (relativeY > targetHeight * 0.75) {
        dropPosition = 'after'
      } else {
        dropPosition = 'inside'
      }

      // Update drop indicator
      updateDropIndicator(dropTarget, dropPosition)

      if (
        state.dropTarget !== dropTarget ||
        state.dropPosition !== dropPosition
      ) {
        state.dropTarget = dropTarget
        state.dropPosition = dropPosition

        sendToParent('dragOver', {
          dragElement: getElementInfo(state.dragElement),
          dropTarget: getElementInfo(dropTarget),
          dropPosition: dropPosition,
          clientX: event.clientX,
          clientY: event.clientY,
        })
      }
    } else {
      removeDropIndicator()
      state.dropTarget = null
      state.dropPosition = null
    }
  }

  /**
   * Handle mouseup event for drop
   */
  function handleMouseUp(event) {
    if (!state.isDragging || !state.dragElement) return

    event.preventDefault()
    event.stopPropagation()

    const dragElement = state.dragElement
    const dropTarget = state.dropTarget
    const dropPosition = state.dropPosition

    // Get element info before moving
    const dragElementInfo = getElementInfo(dragElement)
    const dropTargetInfo = dropTarget ? getElementInfo(dropTarget) : null

    // Calculate movement delta
    const deltaX = event.clientX - state.dragStartX
    const deltaY = event.clientY - state.dragStartY

    // Restore element style
    dragElement.style.opacity = ''
    dragElement.style.pointerEvents = ''
    document.body.style.cursor = ''

    // Remove visual elements
    removeDragGhost()
    removeDropIndicator()

    // Perform the actual DOM move if there's a valid drop target
    let moveSuccess = false
    let newPosition = null

    if (dropTarget && dropPosition) {
      try {
        // Capture state before the move (but don't add to history yet)
        const beforeSnapshot = captureSnapshot(
          'beforeMove',
          `Before moving ${dragElement.tagName.toLowerCase()}`
        )

        if (dropPosition === 'before') {
          dropTarget.parentElement.insertBefore(dragElement, dropTarget)
        } else if (dropPosition === 'after') {
          dropTarget.parentElement.insertBefore(
            dragElement,
            dropTarget.nextSibling
          )
        } else if (dropPosition === 'inside') {
          dropTarget.appendChild(dragElement)
        }

        // DOM operation succeeded - now save history
        moveSuccess = true
        newPosition = {
          parent: getElementInfo(dragElement.parentElement),
          index: Array.from(dragElement.parentElement.children).indexOf(
            dragElement
          ),
        }

        // Add beforeMove snapshot to history (only if DOM operation succeeded)
        if (beforeSnapshot) {
          addSnapshotToHistory(beforeSnapshot)
        }

        // Save state after the move
        saveToHistory(
          'move',
          `Moved ${dragElement.tagName.toLowerCase()} ${dropPosition} ${dropTarget.tagName.toLowerCase()}`
        )

        console.log('[SandboxInspect] Element moved:', dropPosition, 'target')
      } catch (e) {
        console.error('[SandboxInspect] Failed to move element:', e)
        moveSuccess = false
      }
    }

    // Send drag end event with all information
    sendToParent('dragEnd', {
      element: dragElementInfo,
      dropTarget: dropTargetInfo,
      dropPosition: dropPosition,
      deltaX: deltaX,
      deltaY: deltaY,
      moveSuccess: moveSuccess,
      newPosition: newPosition,
      finalRect: getElementRect(dragElement),
    })

    // Update selected element info after move
    if (moveSuccess) {
      const updatedElementInfo = getElementInfo(dragElement)
      if (updatedElementInfo && dragElement.outerHTML) {
        const html = dragElement.outerHTML
        updatedElementInfo.outerHTML =
          html.length > 1000 ? html.slice(0, 1000) + '...' : html
      }
      sendToParent('select', {
        element: updatedElementInfo,
      })
    }

    // Reset drag state
    state.isDragging = false
    state.dragElement = null
    state.dragStartX = 0
    state.dragStartY = 0
    state.dragOffsetX = 0
    state.dragOffsetY = 0
    state.dropTarget = null
    state.dropPosition = null

    console.log('[SandboxInspect] Drag ended')
  }

  /**
   * Create a ghost element for drag visualization
   */
  function createDragGhost(element, x, y) {
    removeDragGhost() // Remove any existing ghost

    const ghost = document.createElement('div')
    ghost.className = '__sandbox-drag-ghost__'

    const rect = element.getBoundingClientRect()
    ghost.style.cssText = `
      position: fixed;
      left: ${x - state.dragOffsetX}px;
      top: ${y - state.dragOffsetY}px;
      width: ${rect.width}px;
      height: ${rect.height}px;
      background: rgba(59, 130, 246, 0.2);
      border: 2px dashed #3b82f6;
      border-radius: 4px;
      pointer-events: none;
      z-index: 10000;
      transition: none;
    `

    document.body.appendChild(ghost)
  }

  /**
   * Update ghost element position
   */
  function updateDragGhost(x, y) {
    const ghost = document.querySelector('.__sandbox-drag-ghost__')
    if (ghost) {
      ghost.style.left = `${x - state.dragOffsetX}px`
      ghost.style.top = `${y - state.dragOffsetY}px`
    }
  }

  /**
   * Remove drag ghost element
   */
  function removeDragGhost() {
    const ghost = document.querySelector('.__sandbox-drag-ghost__')
    if (ghost) {
      ghost.remove()
    }
  }

  /**
   * Update drop indicator
   */
  function updateDropIndicator(target, position) {
    let indicator = document.querySelector('.__sandbox-drop-indicator__')

    if (!indicator) {
      indicator = document.createElement('div')
      indicator.className = '__sandbox-drop-indicator__'
      indicator.style.cssText = `
        position: fixed;
        pointer-events: none;
        z-index: 10001;
        transition: all 0.1s ease;
      `
      document.body.appendChild(indicator)
    }

    const targetRect = target.getBoundingClientRect()

    if (position === 'before') {
      indicator.style.left = `${targetRect.left}px`
      indicator.style.top = `${targetRect.top - 2}px`
      indicator.style.width = `${targetRect.width}px`
      indicator.style.height = '4px'
      indicator.style.background = '#10b981'
      indicator.style.border = 'none'
      indicator.style.borderRadius = '2px'
    } else if (position === 'after') {
      indicator.style.left = `${targetRect.left}px`
      indicator.style.top = `${targetRect.bottom - 2}px`
      indicator.style.width = `${targetRect.width}px`
      indicator.style.height = '4px'
      indicator.style.background = '#10b981'
      indicator.style.border = 'none'
      indicator.style.borderRadius = '2px'
    } else if (position === 'inside') {
      indicator.style.left = `${targetRect.left}px`
      indicator.style.top = `${targetRect.top}px`
      indicator.style.width = `${targetRect.width}px`
      indicator.style.height = `${targetRect.height}px`
      indicator.style.background = 'rgba(16, 185, 129, 0.1)'
      indicator.style.border = '2px solid #10b981'
      indicator.style.borderRadius = '4px'
    }
  }

  /**
   * Remove drop indicator
   */
  function removeDropIndicator() {
    const indicator = document.querySelector('.__sandbox-drop-indicator__')
    if (indicator) {
      indicator.remove()
    }
  }

  /**
   * Handle scroll event (throttled)
   */
  const handleScroll = throttle(function () {
    if (!state.enabled) return

    const updates = {}

    if (state.hoveredElement) {
      updates.hoveredElement = getElementInfo(state.hoveredElement)
    }

    if (state.selectedElement) {
      // Check if element is still in DOM
      if (!document.contains(state.selectedElement)) {
        state.selectedElement = null
        updates.selectedElement = null
      } else {
        updates.selectedElement = getElementInfo(state.selectedElement)
      }
    }

    sendToParent('positionUpdate', updates)
  }, CONFIG.THROTTLE_DELAY)

  /**
   * Handle resize event (throttled)
   */
  const handleResize = throttle(function () {
    if (!state.enabled) return

    const updates = {}

    if (state.hoveredElement) {
      updates.hoveredElement = getElementInfo(state.hoveredElement)
    }

    if (state.selectedElement) {
      if (!document.contains(state.selectedElement)) {
        state.selectedElement = null
        updates.selectedElement = null
      } else {
        updates.selectedElement = getElementInfo(state.selectedElement)
      }
    }

    sendToParent('positionUpdate', updates)
  }, CONFIG.THROTTLE_DELAY)

  /**
   * Use MutationObserver to detect DOM changes
   */
  let mutationObserver = null

  function setupMutationObserver() {
    if (mutationObserver) return

    mutationObserver = new MutationObserver(
      throttle(function (mutations) {
        if (!state.enabled) return

        // Check if selected element was removed
        if (
          state.selectedElement &&
          !document.contains(state.selectedElement)
        ) {
          state.selectedElement = null
          sendToParent('unselect', { element: null, reason: 'removed' })
        }

        // Check if hovered element was removed
        if (state.hoveredElement && !document.contains(state.hoveredElement)) {
          state.hoveredElement = null
          sendToParent('unhover', { element: null, reason: 'removed' })
        }

        // Send position update if elements still exist
        if (state.selectedElement || state.hoveredElement) {
          handleScroll()
        }
      }, 100)
    )

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class'],
    })
  }

  function teardownMutationObserver() {
    if (mutationObserver) {
      mutationObserver.disconnect()
      mutationObserver = null
    }
  }

  // ============================================
  // Edit Mode Control
  // ============================================

  /**
   * Handle input event in edit mode (debounced history save)
   */
  function handleEditInput() {
    if (!state.editMode) return

    const now = Date.now()

    // If this is the start of a new edit batch, reference the "before" state
    // Note: We use the last history entry instead of capturing a new snapshot
    // because MutationObserver fires AFTER the DOM mutation, so capturing now
    // would get the post-edit state, not the pre-edit state
    if (!editModeState.isEditing) {
      editModeState.isEditing = true
      // Use the last history entry as the "before" state
      editModeState.pendingSnapshot =
        historyState.history[historyState.currentIndex] || null
      editModeState.editCount = 0
    }

    editModeState.editCount++
    editModeState.lastEditTime = now

    // Clear existing timer
    if (editModeState.debounceTimer) {
      clearTimeout(editModeState.debounceTimer)
    }

    // Set new timer to save after debounce delay
    editModeState.debounceTimer = setTimeout(() => {
      flushEditHistory()
    }, editModeConfig.debounceDelay)

    // Notify parent of edit activity
    sendToParent('editActivity', {
      editCount: editModeState.editCount,
      pending: true,
    })
  }

  /**
   * Flush pending edit history (save the current edit batch)
   */
  function flushEditHistory() {
    if (!editModeState.isEditing) return

    // Clear timer
    if (editModeState.debounceTimer) {
      clearTimeout(editModeState.debounceTimer)
      editModeState.debounceTimer = null
    }

    // Capture current (post-edit) state
    const currentSnapshot = captureSnapshot('edit', 'Edit changes')

    let didSave = false
    if (
      editModeState.pendingSnapshot &&
      currentSnapshot &&
      editModeState.pendingSnapshot.htmlContent !== currentSnapshot.htmlContent
    ) {
      // pendingSnapshot is a reference to an existing history entry (the pre-edit state),
      // so we only need to save the current post-edit state
      saveToHistory(
        'edit',
        `Edit (${editModeState.editCount} change${editModeState.editCount > 1 ? 's' : ''})`
      )

      console.log(
        `[SandboxInspect] Edit batch saved: ${editModeState.editCount} changes`
      )
      didSave = true
    }

    // Reset edit state
    editModeState.pendingSnapshot = null
    editModeState.editCount = 0
    editModeState.isEditing = false
    editModeState.lastEditTime = 0

    // Notify parent - only report saved: true if we actually saved changes
    sendToParent('editActivity', {
      editCount: 0,
      pending: false,
      saved: didSave,
    })
  }

  /**
   * MutationObserver for edit mode to track DOM changes
   */
  let editModeObserver = null

  function setupEditModeObserver() {
    if (editModeObserver) return

    editModeObserver = new MutationObserver(mutations => {
      if (!state.editMode) return

      // Filter out mutations that are just our own operations
      const hasRealChanges = mutations.some(mutation => {
        // Ignore changes to our inspector elements
        if (
          mutation.target.classList &&
          (mutation.target.classList.contains('__sandbox-drag-ghost__') ||
            mutation.target.classList.contains('__sandbox-drop-indicator__'))
        ) {
          return false
        }
        return true
      })

      if (hasRealChanges) {
        handleEditInput()
      }
    })

    editModeObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      characterData: true,
      characterDataOldValue: true,
    })
  }

  function teardownEditModeObserver() {
    if (editModeObserver) {
      editModeObserver.disconnect()
      editModeObserver = null
    }
  }

  /**
   * Enable edit mode
   */
  function enableEditMode() {
    if (state.editMode) return

    // Disable inspect mode if it's enabled
    if (state.enabled) {
      disableInspectMode()
    }

    state.editMode = true

    // Enable contentEditable on body
    document.body.contentEditable = 'true'

    // Add edit mode styles
    addEditModeStyles()

    // Setup observer to track changes
    setupEditModeObserver()

    // Capture initial state if not already captured
    if (historyState.history.length === 0) {
      captureInitialState()
    }

    sendToParent('editModeEnabled', { editMode: true })
    console.log('[SandboxInspect] Edit mode enabled')
  }

  /**
   * Disable edit mode
   */
  function disableEditMode() {
    if (!state.editMode) return

    // Flush any pending edits before disabling
    flushEditHistory()

    state.editMode = false

    // Disable contentEditable
    document.body.contentEditable = 'false'

    // Remove edit mode styles
    removeEditModeStyles()

    // Teardown observer
    teardownEditModeObserver()

    // Reset edit state
    editModeState.pendingSnapshot = null
    editModeState.editCount = 0
    editModeState.isEditing = false
    if (editModeState.debounceTimer) {
      clearTimeout(editModeState.debounceTimer)
      editModeState.debounceTimer = null
    }

    sendToParent('editModeDisabled', { editMode: false })
    console.log('[SandboxInspect] Edit mode disabled')
  }

  /**
   * Add edit mode visual styles
   */
  function addEditModeStyles() {
    if (document.getElementById('__sandbox-edit-mode-styles__')) return

    const style = document.createElement('style')
    style.id = '__sandbox-edit-mode-styles__'
    style.textContent = `
      body[contenteditable="true"] {
        outline: none;
        cursor: text;
      }
      body[contenteditable="true"] *:hover {
        outline: 1px dashed rgba(59, 130, 246, 0.5);
        outline-offset: 2px;
      }
      body[contenteditable="true"] *:focus {
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
      }
      body[contenteditable="true"]::before {
        content: 'Edit Mode';
        position: fixed;
        top: 8px;
        right: 8px;
        background: #3b82f6;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: system-ui, sans-serif;
        z-index: 10000;
        pointer-events: none;
      }
    `
    document.head.appendChild(style)
  }

  /**
   * Remove edit mode visual styles
   */
  function removeEditModeStyles() {
    const style = document.getElementById('__sandbox-edit-mode-styles__')
    if (style) {
      style.remove()
    }
  }

  // ============================================
  // Inspect Mode Control
  // ============================================

  /**
   * Enable inspect mode
   */
  function enableInspectMode() {
    if (state.enabled) return

    // Disable edit mode if it's enabled
    if (state.editMode) {
      disableEditMode()
    }

    state.enabled = true

    // Add event listeners
    document.addEventListener('mouseover', handleMouseOver, true)
    document.addEventListener('mouseout', handleMouseOut, true)
    document.addEventListener('click', handleClick, true)
    window.addEventListener('scroll', handleScroll, true)
    window.addEventListener('resize', handleResize, true)

    // Add drag event listeners
    document.addEventListener('mousedown', handleMouseDown, true)
    document.addEventListener('mousemove', handleDragMove, true)
    document.addEventListener('mouseup', handleMouseUp, true)

    // Setup mutation observer
    setupMutationObserver()

    // Add visual indicator
    document.body.style.cursor = 'crosshair'

    sendToParent('enabled', { enabled: true })
    console.log('[SandboxInspect] Inspect mode enabled')
  }

  /**
   * Disable inspect mode
   */
  function disableInspectMode() {
    if (!state.enabled) return

    state.enabled = false

    // Remove event listeners
    document.removeEventListener('mouseover', handleMouseOver, true)
    document.removeEventListener('mouseout', handleMouseOut, true)
    document.removeEventListener('click', handleClick, true)
    window.removeEventListener('scroll', handleScroll, true)
    window.removeEventListener('resize', handleResize, true)

    // Remove drag event listeners
    document.removeEventListener('mousedown', handleMouseDown, true)
    document.removeEventListener('mousemove', handleDragMove, true)
    document.removeEventListener('mouseup', handleMouseUp, true)

    // Clean up any drag state
    if (state.isDragging) {
      if (state.dragElement) {
        state.dragElement.style.opacity = ''
        state.dragElement.style.pointerEvents = ''
      }
      document.body.style.cursor = ''
      removeDragGhost()
      removeDropIndicator()
      state.isDragging = false
      state.dragElement = null
      state.dropTarget = null
      state.dropPosition = null
    }

    // Cancel throttled functions
    handleScroll.cancel()
    handleResize.cancel()

    // Teardown mutation observer
    teardownMutationObserver()

    // Clear states
    clearAllStates()

    // Remove visual indicator
    document.body.style.cursor = ''

    sendToParent('disabled', { enabled: false })
    console.log('[SandboxInspect] Inspect mode disabled')
  }

  /**
   * Clear all states
   */
  function clearAllStates() {
    const hadSelection = state.selectedElement !== null
    const hadHover = state.hoveredElement !== null

    state.hoveredElement = null
    state.selectedElement = null

    if (hadSelection || hadHover) {
      sendToParent('cleared', {
        hoveredElement: null,
        selectedElement: null,
      })
    }
  }

  // ============================================
  // Initialization
  // ============================================

  /**
   * Initialize the library
   */
  function init() {
    // Listen for messages from parent
    window.addEventListener('message', handleParentMessage)

    // Preload diff-dom early for faster diff computation
    loadDiffDom().then(success => {
      if (success) {
        console.log('[SandboxInspect] diff-dom preloaded')
      }
    })

    // Capture initial state for history
    captureInitialState()

    // Notify parent that we're ready
    sendToParent('ready', {
      url: window.location.href,
      title: document.title,
      historyInfo: getHistoryInfo(),
    })

    console.log('[SandboxInspect] Library loaded and ready')
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }

  // ============================================
  // Public API (for debugging)
  // ============================================
  window.__SandboxInspect__ = {
    // Inspect mode
    enable: enableInspectMode,
    disable: disableInspectMode,
    clear: clearAllStates,
    getState: () => ({
      enabled: state.enabled,
      editMode: state.editMode,
      hoveredElement: state.hoveredElement,
      selectedElement: state.selectedElement,
    }),
    getElementInfo: getElementInfo,
    getCssPath: getCssPath,
    // History API
    undo: undo,
    redo: redo,
    getHistoryInfo: getHistoryInfo,
    clearHistory: clearHistory,
    saveToHistory: saveToHistory,
    // Edit mode API
    enableEditMode: enableEditMode,
    disableEditMode: disableEditMode,
    flushEditHistory: flushEditHistory,
    isEditMode: () => state.editMode,
  }
})()
