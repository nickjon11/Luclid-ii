'use strict';

// Pairing is intentionally limited to the lifetime of this popup.
// The native host verifies the code on every ping; no secret is persisted.
const pairStatus = document.getElementById('pair-status');
const pairButton = document.getElementById('pair');
const connectionButton = document.getElementById('connection');
const codeInput = document.getElementById('pairing-code');
let sessionToken = null;

function sendNative(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, response => {
      const error = chrome.runtime.lastError;
      if (error) return reject(new Error(error.message));
      if (!response) return reject(new Error('No response from native host'));
      resolve(response);
    });
  });
}

if (pairButton && connectionButton && pairStatus && codeInput) {
  pairButton.addEventListener('click', async () => {
    const token = codeInput.value.trim();
    if (!token) {
      pairStatus.textContent = 'Enter the local pairing code first.';
      return;
    }
    pairButton.disabled = true;
    try {
      const result = await sendNative({type: 'pair', token});
      if (result.paired === true) {
        sessionToken = token;
        pairStatus.textContent = 'Paired with native host for this popup session. Desktop integration is not yet enabled.';
      } else {
        sessionToken = null;
        pairStatus.textContent = result.error || 'Pairing failed.';
      }
    } catch (error) {
      sessionToken = null;
      pairStatus.textContent = error.message;
    } finally {
      codeInput.value = '';
      pairButton.disabled = false;
    }
  });

  connectionButton.addEventListener('click', async () => {
    connectionButton.disabled = true;
    try {
      const result = await sendNative({type: 'ping', token: sessionToken || ''});
      if (!result.ok) {
        pairStatus.textContent = result.error || 'Native host unavailable.';
      } else if (result.paired === true) {
        pairStatus.textContent = 'Native host reachable. Pairing verified for this popup session. Desktop integration is not yet enabled.';
      } else {
        pairStatus.textContent = 'Native host reachable. Pairing required.';
      }
    } catch (error) {
      pairStatus.textContent = error.message;
    } finally {
      connectionButton.disabled = false;
    }
  });
}

// Preserve the original manual, review-first autofill preview.
const status = document.getElementById('status');
const supported = ['full_name', 'first_name', 'last_name', 'email', 'phone'];
function parseFields() {
  const data = JSON.parse(document.getElementById('fields').value);
  if (!data || Array.isArray(data) || typeof data !== 'object') throw new Error('Expected JSON object');
  return Object.fromEntries(Object.entries(data).filter(([key, value]) =>
    supported.includes(key) && typeof value === 'string' && value.length < 300));
}
async function runAutofill(fill) {
  try {
    const values = parseFields();
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    if (!tab?.id || !/^https:\/\//.test(tab.url || '')) throw new Error('Open an HTTPS application page first');
    const result = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: (values, fill) => {
        const aliases = {
          full_name: ['name', 'full_name', 'fullname'],
          first_name: ['first_name', 'firstname', 'given_name'],
          last_name: ['last_name', 'lastname', 'family_name'],
          email: ['email', 'email_address'],
          phone: ['phone', 'telephone', 'mobile']
        };
        const matches = [];
        for (const [key, value] of Object.entries(values)) {
          const input = [...document.querySelectorAll('input')].find(el =>
            !el.disabled && !el.readOnly && ['text', 'email', 'tel', ''].includes(el.type) &&
            [el.name, el.id, el.autocomplete].some(v =>
              aliases[key].includes((v || '').toLowerCase().replace(/[ -]/g, '_'))));
          if (input) {
            matches.push(key);
            if (fill) {
              input.value = value;
              input.dispatchEvent(new Event('input', {bubbles: true}));
              input.dispatchEvent(new Event('change', {bubbles: true}));
            }
          }
        }
        return matches;
      },
      args: [values, fill]
    });
    if (status) status.textContent = (fill ? 'Filled: ' : 'Matched: ') +
      (result[0]?.result?.join(', ') || 'none') + '. Review all fields manually; nothing was submitted.';
  } catch (error) {
    if (status) status.textContent = error.message;
  }
}
const previewButton = document.getElementById('preview');
const fillButton = document.getElementById('fill');
if (previewButton) previewButton.addEventListener('click', () => runAutofill(false));
if (fillButton) fillButton.addEventListener('click', () => runAutofill(true));
