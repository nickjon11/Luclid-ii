const HOST = 'com.luclid_ii.bridge';

chrome.runtime.onMessage.addListener((request, sender, respond) => {
  if (
    sender.id !== chrome.runtime.id ||
    !['ping', 'pair'].includes(request?.type)
  ) {
    return false;
  }

  const message = {
    type: request.type,
    token: String(request.token || '')
  };

  chrome.runtime.sendNativeMessage(HOST, message, result => {
    if (chrome.runtime.lastError) {
      respond({
        ok: false,
        paired: false,
        error: chrome.runtime.lastError.message
      });
    } else {
      respond(
        result || {
          ok: false,
          paired: false,
          error: 'No response from Luclid-ii'
        }
      );
    }
  });

  return true;
});
