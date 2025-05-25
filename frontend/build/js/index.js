(self["webpackChunkask_hn_digest"] = self["webpackChunkask_hn_digest"] || []).push([["index"],{

/***/ "./frontend/src/application/index.js":
/*!*******************************************!*\
  !*** ./frontend/src/application/index.js ***!
  \*******************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _styles_index_css__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../styles/index.css */ "./frontend/src/styles/index.css");
/* harmony import */ var _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @hotwired/stimulus */ "./node_modules/@hotwired/stimulus/dist/stimulus.js");
/* harmony import */ var _hotwired_stimulus_webpack_helpers__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @hotwired/stimulus-webpack-helpers */ "./node_modules/@hotwired/stimulus-webpack-helpers/dist/stimulus-webpack-helpers.js");
/* harmony import */ var _stimulus_components_dropdown__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @stimulus-components/dropdown */ "./node_modules/@stimulus-components/dropdown/dist/stimulus-dropdown.mjs");
/* harmony import */ var _stimulus_components_reveal__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @stimulus-components/reveal */ "./node_modules/@stimulus-components/reveal/dist/stimulus-reveal-controller.mjs");





const application = _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_1__.Application.start();
const context = __webpack_require__("./frontend/src/controllers sync recursive \\.js$");
application.load((0,_hotwired_stimulus_webpack_helpers__WEBPACK_IMPORTED_MODULE_2__.definitionsFromContext)(context));
application.register('dropdown', _stimulus_components_dropdown__WEBPACK_IMPORTED_MODULE_3__["default"]);
application.register('reveal', _stimulus_components_reveal__WEBPACK_IMPORTED_MODULE_4__["default"]);

/***/ }),

/***/ "./frontend/src/controllers sync recursive \\.js$":
/*!**********************************************!*\
  !*** ./frontend/src/controllers/ sync \.js$ ***!
  \**********************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

var map = {
	"./feedback_controller.js": "./frontend/src/controllers/feedback_controller.js",
	"./newsletter_controller.js": "./frontend/src/controllers/newsletter_controller.js",
	"./testing_controller.js": "./frontend/src/controllers/testing_controller.js"
};


function webpackContext(req) {
	var id = webpackContextResolve(req);
	return __webpack_require__(id);
}
function webpackContextResolve(req) {
	if(!__webpack_require__.o(map, req)) {
		var e = new Error("Cannot find module '" + req + "'");
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	}
	return map[req];
}
webpackContext.keys = function webpackContextKeys() {
	return Object.keys(map);
};
webpackContext.resolve = webpackContextResolve;
module.exports = webpackContext;
webpackContext.id = "./frontend/src/controllers sync recursive \\.js$";

/***/ }),

/***/ "./frontend/src/controllers/feedback_controller.js":
/*!*********************************************************!*\
  !*** ./frontend/src/controllers/feedback_controller.js ***!
  \*********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ _Class)
/* harmony export */ });
/* harmony import */ var _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @hotwired/stimulus */ "./node_modules/@hotwired/stimulus/dist/stimulus.js");
/* harmony import */ var _utils_messages__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../utils/messages */ "./frontend/src/utils/messages.js");
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }


class _Class extends _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__.Controller {
  connect() {
    // Initialize the controller
    this.isOpen = false;

    // Bind keyboard event handlers
    this.handleKeydownBound = this.handleKeydown.bind(this);
    document.addEventListener("keydown", this.handleKeydownBound);
  }
  disconnect() {
    // Clean up event listeners when controller disconnects
    document.removeEventListener("keydown", this.handleKeydownBound);
  }
  toggleFeedback() {
    if (this.isOpen) {
      this.closeFeedback();
    } else {
      this.openFeedback();
    }
  }
  openFeedback() {
    // Display the overlay
    this.overlayTarget.classList.remove("opacity-0", "pointer-events-none");
    this.overlayTarget.classList.add("opacity-100", "pointer-events-auto");

    // Scale up the form with animation
    setTimeout(() => {
      this.formContainerTarget.classList.remove("scale-95");
      this.formContainerTarget.classList.add("scale-100");
    }, 10);

    // Focus the input field
    setTimeout(() => {
      this.feedbackInputTarget.focus();
    }, 300);
    this.isOpen = true;
  }
  closeFeedback() {
    // Scale down the form with animation
    this.formContainerTarget.classList.remove("scale-100");
    this.formContainerTarget.classList.add("scale-95");

    // Hide the overlay with animation
    setTimeout(() => {
      this.overlayTarget.classList.remove("opacity-100", "pointer-events-auto");
      this.overlayTarget.classList.add("opacity-0", "pointer-events-none");
    }, 100);
    this.isOpen = false;
  }
  closeIfClickedOutside(event) {
    // Close if clicked outside the form
    if (event.target === this.overlayTarget) {
      this.closeFeedback();
    }
  }
  handleKeydown(event) {
    // Close with Escape key
    if (event.key === "Escape" && this.isOpen) {
      event.preventDefault();
      this.closeFeedback();
    }

    // Submit with Enter key when focused on the textarea (unless Shift is pressed for multiline)
    if (event.key === "Enter" && !event.shiftKey && this.isOpen && document.activeElement === this.feedbackInputTarget) {
      event.preventDefault();
      this.submitFeedback(event);
    }
  }
  submitFeedback(event) {
    event.preventDefault();
    const feedback = this.feedbackInputTarget.value.trim();
    if (!feedback) {
      return;
    }

    // Add loading state
    const submitButton = event.target.tagName === 'BUTTON' ? event.target : this.element.querySelector('button[type="submit"]');
    const originalButtonText = submitButton?.textContent || 'Submit';
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Submitting...';
    }
    fetch('/api/submit-feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      },
      body: JSON.stringify({
        feedback,
        page: window.location.pathname
      })
    }).then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      return response.json();
    }).then(data => {
      this.resetForm();
      this.closeFeedback();
      (0,_utils_messages__WEBPACK_IMPORTED_MODULE_1__.showMessage)(data.message || "Feedback submitted successfully", 'success');
    }).catch(error => {
      console.error('Error:', error);
      (0,_utils_messages__WEBPACK_IMPORTED_MODULE_1__.showMessage)(error.message || "Failed to submit feedback. Please try again later.", 'error');
      // Reset loading state on error
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
      }
    });
  }
  resetForm() {
    this.feedbackInputTarget.value = "";
  }
}
_defineProperty(_Class, "targets", ["toggleButton", "overlay", "formContainer", "feedbackInput"]);

/***/ }),

/***/ "./frontend/src/controllers/newsletter_controller.js":
/*!***********************************************************!*\
  !*** ./frontend/src/controllers/newsletter_controller.js ***!
  \***********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ _Class)
/* harmony export */ });
/* harmony import */ var _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @hotwired/stimulus */ "./node_modules/@hotwired/stimulus/dist/stimulus.js");
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }

class _Class extends _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__.Controller {
  submit(event) {
    event.preventDefault();
    const form = event.target;
    const email = form.email.value.trim();
    if (!email) {
      this.showMessage("Please enter a valid email address.", "error");
      return;
    }
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Adding...';
    fetch("/api/newsletter/subscribe/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
      },
      body: JSON.stringify({
        email
      })
    }).then(async response => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.message || "Subscription failed. Please try again.");
      }
      this.showMessage(data.message, data.status);
      form.reset();
    }).catch(error => {
      this.showMessage(error.message || "Subscription failed. Please try again later.", "error");
    }).finally(() => {
      submitButton.disabled = false;
      submitButton.textContent = originalButtonText;
    });
  }
  showMessage(message, type) {
    if (!this.hasMessageTarget) return;
    this.messageTarget.textContent = message;
    if (message) {
      this.messageTarget.className = `mt-2 text-center ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
    }
  }
}
_defineProperty(_Class, "targets", ["message"]);

/***/ }),

/***/ "./frontend/src/controllers/testing_controller.js":
/*!********************************************************!*\
  !*** ./frontend/src/controllers/testing_controller.js ***!
  \********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @hotwired/stimulus */ "./node_modules/@hotwired/stimulus/dist/stimulus.js");

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (class extends _hotwired_stimulus__WEBPACK_IMPORTED_MODULE_0__.Controller {
  connect() {
    console.log('tesing controller loaded');
  }
});

/***/ }),

/***/ "./frontend/src/styles/index.css":
/*!***************************************!*\
  !*** ./frontend/src/styles/index.css ***!
  \***************************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin

    if(true) {
      (function() {
        var localsJsonString = undefined;
        // 1748178605729
        var cssReload = __webpack_require__(/*! ../../../node_modules/mini-css-extract-plugin/dist/hmr/hotModuleReplacement.js */ "./node_modules/mini-css-extract-plugin/dist/hmr/hotModuleReplacement.js")(module.id, {});
        // only invalidate when locals change
        if (
          module.hot.data &&
          module.hot.data.value &&
          module.hot.data.value !== localsJsonString
        ) {
          module.hot.invalidate();
        } else {
          module.hot.accept();
        }
        module.hot.dispose(function(data) {
          data.value = localsJsonString;
          cssReload();
        });
      })();
    }
  

/***/ }),

/***/ "./frontend/src/utils/messages.js":
/*!****************************************!*\
  !*** ./frontend/src/utils/messages.js ***!
  \****************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   showMessage: () => (/* binding */ showMessage)
/* harmony export */ });
// static/js/utils/messages.js
function showMessage(message, type = 'error') {
  const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();
  const messageId = Date.now();
  const messageHTML = `
    <div data-reveal-target="item" data-message-id="${messageId}" class="rounded-lg border ${type === 'error' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'} p-4 shadow-sm transition-all duration-300 ease-in-out opacity-0 transform translate-x-full max-w-sm">
      <div class="flex items-start">
        <div class="flex-shrink-0 mr-3">
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <circle class="text-gray-200" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12"/>
            <circle class="${type === 'error' ? 'text-red-600' : 'text-green-600'}" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12" data-timer-circle/>
          </svg>
        </div>
        <div class="flex-grow">
          <p class="text-sm ${type === 'error' ? 'text-red-800' : 'text-green-800'}">
            ${message}
          </p>
        </div>
        <div class="flex-shrink-0 ml-3">
          <button onclick="this.closest('[data-reveal-target=item]').remove()" type="button" class="inline-flex justify-center items-center h-5 w-5 rounded-md ${type === 'error' ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} focus:outline-none focus:ring-2 focus:ring-offset-2 ${type === 'error' ? 'focus:ring-red-500' : 'focus:ring-green-500'}">
            <span class="sr-only">Dismiss</span>
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  `;
  messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  setTimeout(() => {
    messageElement.classList.remove('opacity-0', 'translate-x-full');
    startTimer(messageElement);
  }, 100);
}
function createMessagesContainer() {
  const container = document.createElement('div');
  container.className = 'fixed top-4 right-4 z-50 space-y-4 messages-container';
  document.body.appendChild(container);
  return container;
}
function startTimer(item) {
  const timerCircle = item.querySelector('[data-timer-circle]');
  const radius = 10;
  const circumference = 2 * Math.PI * radius;
  timerCircle.style.strokeDasharray = `${circumference} ${circumference}`;
  timerCircle.style.strokeDashoffset = circumference;
  let progress = 0;
  const interval = setInterval(() => {
    if (progress >= 100) {
      clearInterval(interval);
      hideMessage(item);
    } else {
      progress++;
      const offset = circumference - progress / 100 * circumference;
      timerCircle.style.strokeDashoffset = offset;
    }
  }, 50);
}
function hideMessage(item) {
  item.classList.add('opacity-0', 'translate-x-full');
  setTimeout(() => {
    item.remove();
  }, 300);
}

/***/ })

},
/******/ __webpack_require__ => { // webpackRuntimeModules
/******/ var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
/******/ __webpack_require__.O(0, ["vendors-node_modules_hotwired_stimulus-webpack-helpers_dist_stimulus-webpack-helpers_js-node_-9ebed4"], () => (__webpack_exec__("./node_modules/webpack-dev-server/client/index.js?protocol=ws%3A&hostname=0.0.0.0&port=9091&pathname=%2Fws&logging=info&overlay=true&reconnect=10&hot=true&live-reload=true"), __webpack_exec__("./node_modules/webpack/hot/dev-server.js"), __webpack_exec__("./frontend/src/application/index.js")));
/******/ var __webpack_exports__ = __webpack_require__.O();
/******/ }
]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,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Q0UsZ0JBQWdCLEdBQUdMLGFBQWE7RUFFbEQsSUFBSU0sUUFBUSxHQUFHLENBQUM7RUFDaEIsTUFBTUMsUUFBUSxHQUFHQyxXQUFXLENBQUMsTUFBTTtJQUNqQyxJQUFJRixRQUFRLElBQUksR0FBRyxFQUFFO01BQ25CRyxhQUFhLENBQUNGLFFBQVEsQ0FBQztNQUN2QkcsV0FBVyxDQUFDYixJQUFJLENBQUM7SUFDbkIsQ0FBQyxNQUFNO01BQ0xTLFFBQVEsRUFBRTtNQUNWLE1BQU1LLE1BQU0sR0FBR1gsYUFBYSxHQUFJTSxRQUFRLEdBQUcsR0FBRyxHQUFJTixhQUFhO01BQy9ERixXQUFXLENBQUNLLEtBQUssQ0FBQ0UsZ0JBQWdCLEdBQUdNLE1BQU07SUFDN0M7RUFDRixDQUFDLEVBQUUsRUFBRSxDQUFDO0FBQ1I7QUFFQSxTQUFTRCxXQUFXQSxDQUFDYixJQUFJLEVBQUU7RUFDekJBLElBQUksQ0FBQ3ZFLFNBQVMsQ0FBQ0UsR0FBRyxDQUFDLFdBQVcsRUFBRSxrQkFBa0IsQ0FBQztFQUNuREMsVUFBVSxDQUFDLE1BQU07SUFDZm9FLElBQUksQ0FBQ3RFLE1BQU0sQ0FBQyxDQUFDO0VBQ2YsQ0FBQyxFQUFFLEdBQUcsQ0FBQztBQUNUIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vYXNrX2huX2RpZ2VzdC8uL2Zyb250ZW5kL3NyYy9hcHBsaWNhdGlvbi9pbmRleC5qcyIsIndlYnBhY2s6Ly9hc2tfaG5fZGlnZXN0Ly4vZnJvbnRlbmQvc3JjL2NvbnRyb2xsZXJzLyBzeW5jIFxcLmpzJCIsIndlYnBhY2s6Ly9hc2tfaG5fZGlnZXN0Ly4vZnJvbnRlbmQvc3JjL2NvbnRyb2xsZXJzL2ZlZWRiYWNrX2NvbnRyb2xsZXIuanMiLCJ3ZWJwYWNrOi8vYXNrX2huX2RpZ2VzdC8uL2Zyb250ZW5kL3NyYy9jb250cm9sbGVycy9uZXdzbGV0dGVyX2NvbnRyb2xsZXIuanMiLCJ3ZWJwYWNrOi8vYXNrX2huX2RpZ2VzdC8uL2Zyb250ZW5kL3NyYy9jb250cm9sbGVycy90ZXN0aW5nX2NvbnRyb2xsZXIuanMiLCJ3ZWJwYWNrOi8vYXNrX2huX2RpZ2VzdC8uL2Zyb250ZW5kL3NyYy9zdHlsZXMvaW5kZXguY3NzIiwid2VicGFjazovL2Fza19obl9kaWdlc3QvLi9mcm9udGVuZC9zcmMvdXRpbHMvbWVzc2FnZXMuanMiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IFwiLi4vc3R5bGVzL2luZGV4LmNzc1wiO1xuXG5pbXBvcnQgeyBBcHBsaWNhdGlvbiB9IGZyb20gXCJAaG90d2lyZWQvc3RpbXVsdXNcIjtcbmltcG9ydCB7IGRlZmluaXRpb25zRnJvbUNvbnRleHQgfSBmcm9tIFwiQGhvdHdpcmVkL3N0aW11bHVzLXdlYnBhY2staGVscGVyc1wiO1xuXG5pbXBvcnQgRHJvcGRvd24gZnJvbSAnQHN0aW11bHVzLWNvbXBvbmVudHMvZHJvcGRvd24nO1xuaW1wb3J0IFJldmVhbENvbnRyb2xsZXIgZnJvbSAnQHN0aW11bHVzLWNvbXBvbmVudHMvcmV2ZWFsJztcblxuY29uc3QgYXBwbGljYXRpb24gPSBBcHBsaWNhdGlvbi5zdGFydCgpO1xuXG5jb25zdCBjb250ZXh0ID0gcmVxdWlyZS5jb250ZXh0KFwiLi4vY29udHJvbGxlcnNcIiwgdHJ1ZSwgL1xcLmpzJC8pO1xuYXBwbGljYXRpb24ubG9hZChkZWZpbml0aW9uc0Zyb21Db250ZXh0KGNvbnRleHQpKTtcblxuYXBwbGljYXRpb24ucmVnaXN0ZXIoJ2Ryb3Bkb3duJywgRHJvcGRvd24pO1xuYXBwbGljYXRpb24ucmVnaXN0ZXIoJ3JldmVhbCcsIFJldmVhbENvbnRyb2xsZXIpO1xuIiwidmFyIG1hcCA9IHtcblx0XCIuL2ZlZWRiYWNrX2NvbnRyb2xsZXIuanNcIjogXCIuL2Zyb250ZW5kL3NyYy9jb250cm9sbGVycy9mZWVkYmFja19jb250cm9sbGVyLmpzXCIsXG5cdFwiLi9uZXdzbGV0dGVyX2NvbnRyb2xsZXIuanNcIjogXCIuL2Zyb250ZW5kL3NyYy9jb250cm9sbGVycy9uZXdzbGV0dGVyX2NvbnRyb2xsZXIuanNcIixcblx0XCIuL3Rlc3RpbmdfY29udHJvbGxlci5qc1wiOiBcIi4vZnJvbnRlbmQvc3JjL2NvbnRyb2xsZXJzL3Rlc3RpbmdfY29udHJvbGxlci5qc1wiXG59O1xuXG5cbmZ1bmN0aW9uIHdlYnBhY2tDb250ZXh0KHJlcSkge1xuXHR2YXIgaWQgPSB3ZWJwYWNrQ29udGV4dFJlc29sdmUocmVxKTtcblx0cmV0dXJuIF9fd2VicGFja19yZXF1aXJlX18oaWQpO1xufVxuZnVuY3Rpb24gd2VicGFja0NvbnRleHRSZXNvbHZlKHJlcSkge1xuXHRpZighX193ZWJwYWNrX3JlcXVpcmVfXy5vKG1hcCwgcmVxKSkge1xuXHRcdHZhciBlID0gbmV3IEVycm9yKFwiQ2Fubm90IGZpbmQgbW9kdWxlICdcIiArIHJlcSArIFwiJ1wiKTtcblx0XHRlLmNvZGUgPSAnTU9EVUxFX05PVF9GT1VORCc7XG5cdFx0dGhyb3cgZTtcblx0fVxuXHRyZXR1cm4gbWFwW3JlcV07XG59XG53ZWJwYWNrQ29udGV4dC5rZXlzID0gZnVuY3Rpb24gd2VicGFja0NvbnRleHRLZXlzKCkge1xuXHRyZXR1cm4gT2JqZWN0LmtleXMobWFwKTtcbn07XG53ZWJwYWNrQ29udGV4dC5yZXNvbHZlID0gd2VicGFja0NvbnRleHRSZXNvbHZlO1xubW9kdWxlLmV4cG9ydHMgPSB3ZWJwYWNrQ29udGV4dDtcbndlYnBhY2tDb250ZXh0LmlkID0gXCIuL2Zyb250ZW5kL3NyYy9jb250cm9sbGVycyBzeW5jIHJlY3Vyc2l2ZSBcXFxcLmpzJFwiOyIsImltcG9ydCB7IENvbnRyb2xsZXIgfSBmcm9tIFwiQGhvdHdpcmVkL3N0aW11bHVzXCI7XG5pbXBvcnQgeyBzaG93TWVzc2FnZSB9IGZyb20gXCIuLi91dGlscy9tZXNzYWdlc1wiO1xuXG5leHBvcnQgZGVmYXVsdCBjbGFzcyBleHRlbmRzIENvbnRyb2xsZXIge1xuICBzdGF0aWMgdGFyZ2V0cyA9IFtcInRvZ2dsZUJ1dHRvblwiLCBcIm92ZXJsYXlcIiwgXCJmb3JtQ29udGFpbmVyXCIsIFwiZmVlZGJhY2tJbnB1dFwiXTtcblxuICBjb25uZWN0KCkge1xuICAgIC8vIEluaXRpYWxpemUgdGhlIGNvbnRyb2xsZXJcbiAgICB0aGlzLmlzT3BlbiA9IGZhbHNlO1xuXG4gICAgLy8gQmluZCBrZXlib2FyZCBldmVudCBoYW5kbGVyc1xuICAgIHRoaXMuaGFuZGxlS2V5ZG93bkJvdW5kID0gdGhpcy5oYW5kbGVLZXlkb3duLmJpbmQodGhpcyk7XG4gICAgZG9jdW1lbnQuYWRkRXZlbnRMaXN0ZW5lcihcImtleWRvd25cIiwgdGhpcy5oYW5kbGVLZXlkb3duQm91bmQpO1xuICB9XG5cbiAgZGlzY29ubmVjdCgpIHtcbiAgICAvLyBDbGVhbiB1cCBldmVudCBsaXN0ZW5lcnMgd2hlbiBjb250cm9sbGVyIGRpc2Nvbm5lY3RzXG4gICAgZG9jdW1lbnQucmVtb3ZlRXZlbnRMaXN0ZW5lcihcImtleWRvd25cIiwgdGhpcy5oYW5kbGVLZXlkb3duQm91bmQpO1xuICB9XG5cbiAgdG9nZ2xlRmVlZGJhY2soKSB7XG4gICAgaWYgKHRoaXMuaXNPcGVuKSB7XG4gICAgICB0aGlzLmNsb3NlRmVlZGJhY2soKTtcbiAgICB9IGVsc2Uge1xuICAgICAgdGhpcy5vcGVuRmVlZGJhY2soKTtcbiAgICB9XG4gIH1cblxuICBvcGVuRmVlZGJhY2soKSB7XG4gICAgLy8gRGlzcGxheSB0aGUgb3ZlcmxheVxuICAgIHRoaXMub3ZlcmxheVRhcmdldC5jbGFzc0xpc3QucmVtb3ZlKFwib3BhY2l0eS0wXCIsIFwicG9pbnRlci1ldmVudHMtbm9uZVwiKTtcbiAgICB0aGlzLm92ZXJsYXlUYXJnZXQuY2xhc3NMaXN0LmFkZChcIm9wYWNpdHktMTAwXCIsIFwicG9pbnRlci1ldmVudHMtYXV0b1wiKTtcblxuICAgIC8vIFNjYWxlIHVwIHRoZSBmb3JtIHdpdGggYW5pbWF0aW9uXG4gICAgc2V0VGltZW91dCgoKSA9PiB7XG4gICAgICB0aGlzLmZvcm1Db250YWluZXJUYXJnZXQuY2xhc3NMaXN0LnJlbW92ZShcInNjYWxlLTk1XCIpO1xuICAgICAgdGhpcy5mb3JtQ29udGFpbmVyVGFyZ2V0LmNsYXNzTGlzdC5hZGQoXCJzY2FsZS0xMDBcIik7XG4gICAgfSwgMTApO1xuXG4gICAgLy8gRm9jdXMgdGhlIGlucHV0IGZpZWxkXG4gICAgc2V0VGltZW91dCgoKSA9PiB7XG4gICAgICB0aGlzLmZlZWRiYWNrSW5wdXRUYXJnZXQuZm9jdXMoKTtcbiAgICB9LCAzMDApO1xuXG4gICAgdGhpcy5pc09wZW4gPSB0cnVlO1xuICB9XG5cbiAgY2xvc2VGZWVkYmFjaygpIHtcbiAgICAvLyBTY2FsZSBkb3duIHRoZSBmb3JtIHdpdGggYW5pbWF0aW9uXG4gICAgdGhpcy5mb3JtQ29udGFpbmVyVGFyZ2V0LmNsYXNzTGlzdC5yZW1vdmUoXCJzY2FsZS0xMDBcIik7XG4gICAgdGhpcy5mb3JtQ29udGFpbmVyVGFyZ2V0LmNsYXNzTGlzdC5hZGQoXCJzY2FsZS05NVwiKTtcblxuICAgIC8vIEhpZGUgdGhlIG92ZXJsYXkgd2l0aCBhbmltYXRpb25cbiAgICBzZXRUaW1lb3V0KCgpID0+IHtcbiAgICAgIHRoaXMub3ZlcmxheVRhcmdldC5jbGFzc0xpc3QucmVtb3ZlKFwib3BhY2l0eS0xMDBcIiwgXCJwb2ludGVyLWV2ZW50cy1hdXRvXCIpO1xuICAgICAgdGhpcy5vdmVybGF5VGFyZ2V0LmNsYXNzTGlzdC5hZGQoXCJvcGFjaXR5LTBcIiwgXCJwb2ludGVyLWV2ZW50cy1ub25lXCIpO1xuICAgIH0sIDEwMCk7XG5cbiAgICB0aGlzLmlzT3BlbiA9IGZhbHNlO1xuICB9XG5cbiAgY2xvc2VJZkNsaWNrZWRPdXRzaWRlKGV2ZW50KSB7XG4gICAgLy8gQ2xvc2UgaWYgY2xpY2tlZCBvdXRzaWRlIHRoZSBmb3JtXG4gICAgaWYgKGV2ZW50LnRhcmdldCA9PT0gdGhpcy5vdmVybGF5VGFyZ2V0KSB7XG4gICAgICB0aGlzLmNsb3NlRmVlZGJhY2soKTtcbiAgICB9XG4gIH1cblxuICBoYW5kbGVLZXlkb3duKGV2ZW50KSB7XG4gICAgLy8gQ2xvc2Ugd2l0aCBFc2NhcGUga2V5XG4gICAgaWYgKGV2ZW50LmtleSA9PT0gXCJFc2NhcGVcIiAmJiB0aGlzLmlzT3Blbikge1xuICAgICAgZXZlbnQucHJldmVudERlZmF1bHQoKTtcbiAgICAgIHRoaXMuY2xvc2VGZWVkYmFjaygpO1xuICAgIH1cblxuICAgIC8vIFN1Ym1pdCB3aXRoIEVudGVyIGtleSB3aGVuIGZvY3VzZWQgb24gdGhlIHRleHRhcmVhICh1bmxlc3MgU2hpZnQgaXMgcHJlc3NlZCBmb3IgbXVsdGlsaW5lKVxuICAgIGlmIChldmVudC5rZXkgPT09IFwiRW50ZXJcIiAmJiAhZXZlbnQuc2hpZnRLZXkgJiYgdGhpcy5pc09wZW4gJiZcbiAgICAgICAgZG9jdW1lbnQuYWN0aXZlRWxlbWVudCA9PT0gdGhpcy5mZWVkYmFja0lucHV0VGFyZ2V0KSB7XG4gICAgICBldmVudC5wcmV2ZW50RGVmYXVsdCgpO1xuICAgICAgdGhpcy5zdWJtaXRGZWVkYmFjayhldmVudCk7XG4gICAgfVxuICB9XG5cbiAgc3VibWl0RmVlZGJhY2soZXZlbnQpIHtcbiAgICBldmVudC5wcmV2ZW50RGVmYXVsdCgpO1xuXG4gICAgY29uc3QgZmVlZGJhY2sgPSB0aGlzLmZlZWRiYWNrSW5wdXRUYXJnZXQudmFsdWUudHJpbSgpO1xuXG4gICAgaWYgKCFmZWVkYmFjaykge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIC8vIEFkZCBsb2FkaW5nIHN0YXRlXG4gICAgY29uc3Qgc3VibWl0QnV0dG9uID0gZXZlbnQudGFyZ2V0LnRhZ05hbWUgPT09ICdCVVRUT04nID8gZXZlbnQudGFyZ2V0IDogdGhpcy5lbGVtZW50LnF1ZXJ5U2VsZWN0b3IoJ2J1dHRvblt0eXBlPVwic3VibWl0XCJdJyk7XG4gICAgY29uc3Qgb3JpZ2luYWxCdXR0b25UZXh0ID0gc3VibWl0QnV0dG9uPy50ZXh0Q29udGVudCB8fCAnU3VibWl0JztcbiAgICBpZiAoc3VibWl0QnV0dG9uKSB7XG4gICAgICBzdWJtaXRCdXR0b24uZGlzYWJsZWQgPSB0cnVlO1xuICAgICAgc3VibWl0QnV0dG9uLnRleHRDb250ZW50ID0gJ1N1Ym1pdHRpbmcuLi4nO1xuICAgIH1cblxuICAgIGZldGNoKCcvYXBpL3N1Ym1pdC1mZWVkYmFjaycsIHtcbiAgICAgIG1ldGhvZDogJ1BPU1QnLFxuICAgICAgaGVhZGVyczoge1xuICAgICAgICAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nLFxuICAgICAgICAnWC1DU1JGVG9rZW4nOiBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdbbmFtZT1jc3JmbWlkZGxld2FyZXRva2VuXScpLnZhbHVlXG4gICAgICB9LFxuICAgICAgYm9keTogSlNPTi5zdHJpbmdpZnkoeyBmZWVkYmFjaywgcGFnZTogd2luZG93LmxvY2F0aW9uLnBhdGhuYW1lIH0pLFxuICAgIH0pXG4gICAgLnRoZW4ocmVzcG9uc2UgPT4ge1xuICAgICAgaWYgKCFyZXNwb25zZS5vaykge1xuICAgICAgICB0aHJvdyBuZXcgRXJyb3IoYFNlcnZlciByZXNwb25kZWQgd2l0aCAke3Jlc3BvbnNlLnN0YXR1c306ICR7cmVzcG9uc2Uuc3RhdHVzVGV4dH1gKTtcbiAgICAgIH1cbiAgICAgIHJldHVybiByZXNwb25zZS5qc29uKCk7XG4gICAgfSlcbiAgICAudGhlbihkYXRhID0+IHtcbiAgICAgIHRoaXMucmVzZXRGb3JtKCk7XG4gICAgICB0aGlzLmNsb3NlRmVlZGJhY2soKTtcbiAgICAgIHNob3dNZXNzYWdlKGRhdGEubWVzc2FnZSB8fCBcIkZlZWRiYWNrIHN1Ym1pdHRlZCBzdWNjZXNzZnVsbHlcIiwgJ3N1Y2Nlc3MnKTtcbiAgICB9KVxuICAgIC5jYXRjaCgoZXJyb3IpID0+IHtcbiAgICAgIGNvbnNvbGUuZXJyb3IoJ0Vycm9yOicsIGVycm9yKTtcbiAgICAgIHNob3dNZXNzYWdlKGVycm9yLm1lc3NhZ2UgfHwgXCJGYWlsZWQgdG8gc3VibWl0IGZlZWRiYWNrLiBQbGVhc2UgdHJ5IGFnYWluIGxhdGVyLlwiLCAnZXJyb3InKTtcbiAgICAgIC8vIFJlc2V0IGxvYWRpbmcgc3RhdGUgb24gZXJyb3JcbiAgICAgIGlmIChzdWJtaXRCdXR0b24pIHtcbiAgICAgICAgc3VibWl0QnV0dG9uLmRpc2FibGVkID0gZmFsc2U7XG4gICAgICAgIHN1Ym1pdEJ1dHRvbi50ZXh0Q29udGVudCA9IG9yaWdpbmFsQnV0dG9uVGV4dDtcbiAgICAgIH1cbiAgICB9KTtcbiAgfVxuXG4gIHJlc2V0Rm9ybSgpIHtcbiAgICB0aGlzLmZlZWRiYWNrSW5wdXRUYXJnZXQudmFsdWUgPSBcIlwiO1xuICB9XG59XG4iLCJpbXBvcnQgeyBDb250cm9sbGVyIH0gZnJvbSBcIkBob3R3aXJlZC9zdGltdWx1c1wiO1xuXG5leHBvcnQgZGVmYXVsdCBjbGFzcyBleHRlbmRzIENvbnRyb2xsZXIge1xuICBzdGF0aWMgdGFyZ2V0cyA9IFtcIm1lc3NhZ2VcIl07XG5cbiAgc3VibWl0KGV2ZW50KSB7XG4gICAgZXZlbnQucHJldmVudERlZmF1bHQoKTtcbiAgICBjb25zdCBmb3JtID0gZXZlbnQudGFyZ2V0O1xuICAgIGNvbnN0IGVtYWlsID0gZm9ybS5lbWFpbC52YWx1ZS50cmltKCk7XG4gICAgaWYgKCFlbWFpbCkge1xuICAgICAgdGhpcy5zaG93TWVzc2FnZShcIlBsZWFzZSBlbnRlciBhIHZhbGlkIGVtYWlsIGFkZHJlc3MuXCIsIFwiZXJyb3JcIik7XG4gICAgICByZXR1cm47XG4gICAgfVxuICAgIGNvbnN0IHN1Ym1pdEJ1dHRvbiA9IGZvcm0ucXVlcnlTZWxlY3RvcignYnV0dG9uW3R5cGU9XCJzdWJtaXRcIl0nKTtcbiAgICBjb25zdCBvcmlnaW5hbEJ1dHRvblRleHQgPSBzdWJtaXRCdXR0b24udGV4dENvbnRlbnQ7XG4gICAgc3VibWl0QnV0dG9uLmRpc2FibGVkID0gdHJ1ZTtcbiAgICBzdWJtaXRCdXR0b24udGV4dENvbnRlbnQgPSAnQWRkaW5nLi4uJztcbiAgICBmZXRjaChcIi9hcGkvbmV3c2xldHRlci9zdWJzY3JpYmUvXCIsIHtcbiAgICAgIG1ldGhvZDogXCJQT1NUXCIsXG4gICAgICBoZWFkZXJzOiB7XG4gICAgICAgIFwiQ29udGVudC1UeXBlXCI6IFwiYXBwbGljYXRpb24vanNvblwiLFxuICAgICAgICAnWC1DU1JGVG9rZW4nOiBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCdbbmFtZT1jc3JmbWlkZGxld2FyZXRva2VuXScpPy52YWx1ZSB8fCAnJ1xuICAgICAgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsgZW1haWwgfSksXG4gICAgfSlcbiAgICAgIC50aGVuKGFzeW5jIChyZXNwb25zZSkgPT4ge1xuICAgICAgICBjb25zdCBkYXRhID0gYXdhaXQgcmVzcG9uc2UuanNvbigpLmNhdGNoKCgpID0+ICh7fSkpO1xuICAgICAgICBpZiAoIXJlc3BvbnNlLm9rKSB7XG4gICAgICAgICAgdGhyb3cgbmV3IEVycm9yKGRhdGEubWVzc2FnZSB8fCBcIlN1YnNjcmlwdGlvbiBmYWlsZWQuIFBsZWFzZSB0cnkgYWdhaW4uXCIpO1xuICAgICAgICB9XG4gICAgICAgIHRoaXMuc2hvd01lc3NhZ2UoXG4gICAgICAgICAgZGF0YS5tZXNzYWdlLFxuICAgICAgICAgIGRhdGEuc3RhdHVzXG4gICAgICAgICk7XG4gICAgICAgIGZvcm0ucmVzZXQoKTtcbiAgICAgIH0pXG4gICAgICAuY2F0Y2goKGVycm9yKSA9PiB7XG4gICAgICAgIHRoaXMuc2hvd01lc3NhZ2UoZXJyb3IubWVzc2FnZSB8fCBcIlN1YnNjcmlwdGlvbiBmYWlsZWQuIFBsZWFzZSB0cnkgYWdhaW4gbGF0ZXIuXCIsIFwiZXJyb3JcIik7XG4gICAgICB9KVxuICAgICAgLmZpbmFsbHkoKCkgPT4ge1xuICAgICAgICBzdWJtaXRCdXR0b24uZGlzYWJsZWQgPSBmYWxzZTtcbiAgICAgICAgc3VibWl0QnV0dG9uLnRleHRDb250ZW50ID0gb3JpZ2luYWxCdXR0b25UZXh0O1xuICAgICAgfSk7XG4gIH1cblxuICBzaG93TWVzc2FnZShtZXNzYWdlLCB0eXBlKSB7XG4gICAgaWYgKCF0aGlzLmhhc01lc3NhZ2VUYXJnZXQpIHJldHVybjtcbiAgICB0aGlzLm1lc3NhZ2VUYXJnZXQudGV4dENvbnRlbnQgPSBtZXNzYWdlO1xuICAgIGlmIChtZXNzYWdlKSB7XG4gICAgICB0aGlzLm1lc3NhZ2VUYXJnZXQuY2xhc3NOYW1lID0gYG10LTIgdGV4dC1jZW50ZXIgJHt0eXBlID09PSAnc3VjY2VzcycgPyAndGV4dC1ncmVlbi02MDAnIDogJ3RleHQtcmVkLTYwMCd9YDtcbiAgICB9XG4gIH1cbn1cbiIsImltcG9ydCB7IENvbnRyb2xsZXIgfSBmcm9tIFwiQGhvdHdpcmVkL3N0aW11bHVzXCI7XG5cbmV4cG9ydCBkZWZhdWx0IGNsYXNzIGV4dGVuZHMgQ29udHJvbGxlciB7XG4gICAgY29ubmVjdCgpIHtcbiAgICAgIGNvbnNvbGUubG9nKCd0ZXNpbmcgY29udHJvbGxlciBsb2FkZWQnKTtcbiAgICB9XG59XG4iLCIvLyBleHRyYWN0ZWQgYnkgbWluaS1jc3MtZXh0cmFjdC1wbHVnaW5cbmV4cG9ydCB7fTtcbiAgICBpZihtb2R1bGUuaG90KSB7XG4gICAgICAoZnVuY3Rpb24oKSB7XG4gICAgICAgIHZhciBsb2NhbHNKc29uU3RyaW5nID0gdW5kZWZpbmVkO1xuICAgICAgICAvLyAxNzQ4MTc4NjA1NzI5XG4gICAgICAgIHZhciBjc3NSZWxvYWQgPSByZXF1aXJlKFwiLi4vLi4vLi4vbm9kZV9tb2R1bGVzL21pbmktY3NzLWV4dHJhY3QtcGx1Z2luL2Rpc3QvaG1yL2hvdE1vZHVsZVJlcGxhY2VtZW50LmpzXCIpKG1vZHVsZS5pZCwge30pO1xuICAgICAgICAvLyBvbmx5IGludmFsaWRhdGUgd2hlbiBsb2NhbHMgY2hhbmdlXG4gICAgICAgIGlmIChcbiAgICAgICAgICBtb2R1bGUuaG90LmRhdGEgJiZcbiAgICAgICAgICBtb2R1bGUuaG90LmRhdGEudmFsdWUgJiZcbiAgICAgICAgICBtb2R1bGUuaG90LmRhdGEudmFsdWUgIT09IGxvY2Fsc0pzb25TdHJpbmdcbiAgICAgICAgKSB7XG4gICAgICAgICAgbW9kdWxlLmhvdC5pbnZhbGlkYXRlKCk7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgbW9kdWxlLmhvdC5hY2NlcHQoKTtcbiAgICAgICAgfVxuICAgICAgICBtb2R1bGUuaG90LmRpc3Bvc2UoZnVuY3Rpb24oZGF0YSkge1xuICAgICAgICAgIGRhdGEudmFsdWUgPSBsb2NhbHNKc29uU3RyaW5nO1xuICAgICAgICAgIGNzc1JlbG9hZCgpO1xuICAgICAgICB9KTtcbiAgICAgIH0pKCk7XG4gICAgfVxuICAiLCIvLyBzdGF0aWMvanMvdXRpbHMvbWVzc2FnZXMuanNcbmV4cG9ydCBmdW5jdGlvbiBzaG93TWVzc2FnZShtZXNzYWdlLCB0eXBlID0gJ2Vycm9yJykge1xuICBjb25zdCBtZXNzYWdlc0NvbnRhaW5lciA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoJy5tZXNzYWdlcy1jb250YWluZXInKSB8fCBjcmVhdGVNZXNzYWdlc0NvbnRhaW5lcigpO1xuXG4gIGNvbnN0IG1lc3NhZ2VJZCA9IERhdGUubm93KCk7XG4gIGNvbnN0IG1lc3NhZ2VIVE1MID0gYFxuICAgIDxkaXYgZGF0YS1yZXZlYWwtdGFyZ2V0PVwiaXRlbVwiIGRhdGEtbWVzc2FnZS1pZD1cIiR7bWVzc2FnZUlkfVwiIGNsYXNzPVwicm91bmRlZC1sZyBib3JkZXIgJHt0eXBlID09PSAnZXJyb3InID8gJ2JnLXJlZC01MCBib3JkZXItcmVkLTIwMCcgOiAnYmctZ3JlZW4tNTAgYm9yZGVyLWdyZWVuLTIwMCd9IHAtNCBzaGFkb3ctc20gdHJhbnNpdGlvbi1hbGwgZHVyYXRpb24tMzAwIGVhc2UtaW4tb3V0IG9wYWNpdHktMCB0cmFuc2Zvcm0gdHJhbnNsYXRlLXgtZnVsbCBtYXgtdy1zbVwiPlxuICAgICAgPGRpdiBjbGFzcz1cImZsZXggaXRlbXMtc3RhcnRcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cImZsZXgtc2hyaW5rLTAgbXItM1wiPlxuICAgICAgICAgIDxzdmcgY2xhc3M9XCJ3LTUgaC01XCIgdmlld0JveD1cIjAgMCAyNCAyNFwiPlxuICAgICAgICAgICAgPGNpcmNsZSBjbGFzcz1cInRleHQtZ3JheS0yMDBcIiBzdHJva2Utd2lkdGg9XCIyXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCIgZmlsbD1cInRyYW5zcGFyZW50XCIgcj1cIjEwXCIgY3g9XCIxMlwiIGN5PVwiMTJcIi8+XG4gICAgICAgICAgICA8Y2lyY2xlIGNsYXNzPVwiJHt0eXBlID09PSAnZXJyb3InID8gJ3RleHQtcmVkLTYwMCcgOiAndGV4dC1ncmVlbi02MDAnfVwiIHN0cm9rZS13aWR0aD1cIjJcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIiBmaWxsPVwidHJhbnNwYXJlbnRcIiByPVwiMTBcIiBjeD1cIjEyXCIgY3k9XCIxMlwiIGRhdGEtdGltZXItY2lyY2xlLz5cbiAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJmbGV4LWdyb3dcIj5cbiAgICAgICAgICA8cCBjbGFzcz1cInRleHQtc20gJHt0eXBlID09PSAnZXJyb3InID8gJ3RleHQtcmVkLTgwMCcgOiAndGV4dC1ncmVlbi04MDAnfVwiPlxuICAgICAgICAgICAgJHttZXNzYWdlfVxuICAgICAgICAgIDwvcD5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJmbGV4LXNocmluay0wIG1sLTNcIj5cbiAgICAgICAgICA8YnV0dG9uIG9uY2xpY2s9XCJ0aGlzLmNsb3Nlc3QoJ1tkYXRhLXJldmVhbC10YXJnZXQ9aXRlbV0nKS5yZW1vdmUoKVwiIHR5cGU9XCJidXR0b25cIiBjbGFzcz1cImlubGluZS1mbGV4IGp1c3RpZnktY2VudGVyIGl0ZW1zLWNlbnRlciBoLTUgdy01IHJvdW5kZWQtbWQgJHt0eXBlID09PSAnZXJyb3InID8gJ3RleHQtcmVkLTYwMCBob3Zlcjp0ZXh0LXJlZC04MDAnIDogJ3RleHQtZ3JlZW4tNjAwIGhvdmVyOnRleHQtZ3JlZW4tODAwJ30gZm9jdXM6b3V0bGluZS1ub25lIGZvY3VzOnJpbmctMiBmb2N1czpyaW5nLW9mZnNldC0yICR7dHlwZSA9PT0gJ2Vycm9yJyA/ICdmb2N1czpyaW5nLXJlZC01MDAnIDogJ2ZvY3VzOnJpbmctZ3JlZW4tNTAwJ31cIj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwic3Itb25seVwiPkRpc21pc3M8L3NwYW4+XG4gICAgICAgICAgICA8c3ZnIGNsYXNzPVwidy00IGgtNFwiIHhtbG5zPVwiaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmdcIiBmaWxsPVwibm9uZVwiIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cbiAgICAgICAgICAgICAgPHBhdGggc3Ryb2tlLWxpbmVjYXA9XCJyb3VuZFwiIHN0cm9rZS1saW5lam9pbj1cInJvdW5kXCIgc3Ryb2tlLXdpZHRoPVwiMlwiIGQ9XCJNNiAxOEwxOCA2TTYgNmwxMiAxMlwiIC8+XG4gICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cbiAgYDtcblxuICBtZXNzYWdlc0NvbnRhaW5lci5pbnNlcnRBZGphY2VudEhUTUwoJ2JlZm9yZWVuZCcsIG1lc3NhZ2VIVE1MKTtcblxuICBjb25zdCBtZXNzYWdlRWxlbWVudCA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoYFtkYXRhLW1lc3NhZ2UtaWQ9XCIke21lc3NhZ2VJZH1cIl1gKTtcbiAgc2V0VGltZW91dCgoKSA9PiB7XG4gICAgbWVzc2FnZUVsZW1lbnQuY2xhc3NMaXN0LnJlbW92ZSgnb3BhY2l0eS0wJywgJ3RyYW5zbGF0ZS14LWZ1bGwnKTtcbiAgICBzdGFydFRpbWVyKG1lc3NhZ2VFbGVtZW50KTtcbiAgfSwgMTAwKTtcbn1cblxuZnVuY3Rpb24gY3JlYXRlTWVzc2FnZXNDb250YWluZXIoKSB7XG4gIGNvbnN0IGNvbnRhaW5lciA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2RpdicpO1xuICBjb250YWluZXIuY2xhc3NOYW1lID0gJ2ZpeGVkIHRvcC00IHJpZ2h0LTQgei01MCBzcGFjZS15LTQgbWVzc2FnZXMtY29udGFpbmVyJztcbiAgZG9jdW1lbnQuYm9keS5hcHBlbmRDaGlsZChjb250YWluZXIpO1xuICByZXR1cm4gY29udGFpbmVyO1xufVxuXG5mdW5jdGlvbiBzdGFydFRpbWVyKGl0ZW0pIHtcbiAgY29uc3QgdGltZXJDaXJjbGUgPSBpdGVtLnF1ZXJ5U2VsZWN0b3IoJ1tkYXRhLXRpbWVyLWNpcmNsZV0nKTtcbiAgY29uc3QgcmFkaXVzID0gMTA7XG4gIGNvbnN0IGNpcmN1bWZlcmVuY2UgPSAyICogTWF0aC5QSSAqIHJhZGl1cztcblxuICB0aW1lckNpcmNsZS5zdHlsZS5zdHJva2VEYXNoYXJyYXkgPSBgJHtjaXJjdW1mZXJlbmNlfSAke2NpcmN1bWZlcmVuY2V9YDtcbiAgdGltZXJDaXJjbGUuc3R5bGUuc3Ryb2tlRGFzaG9mZnNldCA9IGNpcmN1bWZlcmVuY2U7XG5cbiAgbGV0IHByb2dyZXNzID0gMDtcbiAgY29uc3QgaW50ZXJ2YWwgPSBzZXRJbnRlcnZhbCgoKSA9PiB7XG4gICAgaWYgKHByb2dyZXNzID49IDEwMCkge1xuICAgICAgY2xlYXJJbnRlcnZhbChpbnRlcnZhbCk7XG4gICAgICBoaWRlTWVzc2FnZShpdGVtKTtcbiAgICB9IGVsc2Uge1xuICAgICAgcHJvZ3Jlc3MrKztcbiAgICAgIGNvbnN0IG9mZnNldCA9IGNpcmN1bWZlcmVuY2UgLSAocHJvZ3Jlc3MgLyAxMDApICogY2lyY3VtZmVyZW5jZTtcbiAgICAgIHRpbWVyQ2lyY2xlLnN0eWxlLnN0cm9rZURhc2hvZmZzZXQgPSBvZmZzZXQ7XG4gICAgfVxuICB9LCA1MCk7XG59XG5cbmZ1bmN0aW9uIGhpZGVNZXNzYWdlKGl0ZW0pIHtcbiAgaXRlbS5jbGFzc0xpc3QuYWRkKCdvcGFjaXR5LTAnLCAndHJhbnNsYXRlLXgtZnVsbCcpO1xuICBzZXRUaW1lb3V0KCgpID0+IHtcbiAgICBpdGVtLnJlbW92ZSgpO1xuICB9LCAzMDApO1xufVxuIl0sIm5hbWVzIjpbIkFwcGxpY2F0aW9uIiwiZGVmaW5pdGlvbnNGcm9tQ29udGV4dCIsIkRyb3Bkb3duIiwiUmV2ZWFsQ29udHJvbGxlciIsImFwcGxpY2F0aW9uIiwic3RhcnQiLCJjb250ZXh0IiwicmVxdWlyZSIsImxvYWQiLCJyZWdpc3RlciIsIkNvbnRyb2xsZXIiLCJzaG93TWVzc2FnZSIsIl9DbGFzcyIsImNvbm5lY3QiLCJpc09wZW4iLCJoYW5kbGVLZXlkb3duQm91bmQiLCJoYW5kbGVLZXlkb3duIiwiYmluZCIsImRvY3VtZW50IiwiYWRkRXZlbnRMaXN0ZW5lciIsImRpc2Nvbm5lY3QiLCJyZW1vdmVFdmVudExpc3RlbmVyIiwidG9nZ2xlRmVlZGJhY2siLCJjbG9zZUZlZWRiYWNrIiwib3BlbkZlZWRiYWNrIiwib3ZlcmxheVRhcmdldCIsImNsYXNzTGlzdCIsInJlbW92ZSIsImFkZCIsInNldFRpbWVvdXQiLCJmb3JtQ29udGFpbmVyVGFyZ2V0IiwiZmVlZGJhY2tJbnB1dFRhcmdldCIsImZvY3VzIiwiY2xvc2VJZkNsaWNrZWRPdXRzaWRlIiwiZXZlbnQiLCJ0YXJnZXQiLCJrZXkiLCJwcmV2ZW50RGVmYXVsdCIsInNoaWZ0S2V5IiwiYWN0aXZlRWxlbWVudCIsInN1Ym1pdEZlZWRiYWNrIiwiZmVlZGJhY2siLCJ2YWx1ZSIsInRyaW0iLCJzdWJtaXRCdXR0b24iLCJ0YWdOYW1lIiwiZWxlbWVudCIsInF1ZXJ5U2VsZWN0b3IiLCJvcmlnaW5hbEJ1dHRvblRleHQiLCJ0ZXh0Q29udGVudCIsImRpc2FibGVkIiwiZmV0Y2giLCJtZXRob2QiLCJoZWFkZXJzIiwiYm9keSIsIkpTT04iLCJzdHJpbmdpZnkiLCJwYWdlIiwid2luZG93IiwibG9jYXRpb24iLCJwYXRobmFtZSIsInRoZW4iLCJyZXNwb25zZSIsIm9rIiwiRXJyb3IiLCJzdGF0dXMiLCJzdGF0dXNUZXh0IiwianNvbiIsImRhdGEiLCJyZXNldEZvcm0iLCJtZXNzYWdlIiwiY2F0Y2giLCJlcnJvciIsImNvbnNvbGUiLCJfZGVmaW5lUHJvcGVydHkiLCJzdWJtaXQiLCJmb3JtIiwiZW1haWwiLCJyZXNldCIsImZpbmFsbHkiLCJ0eXBlIiwiaGFzTWVzc2FnZVRhcmdldCIsIm1lc3NhZ2VUYXJnZXQiLCJjbGFzc05hbWUiLCJsb2ciLCJtZXNzYWdlc0NvbnRhaW5lciIsImNyZWF0ZU1lc3NhZ2VzQ29udGFpbmVyIiwibWVzc2FnZUlkIiwiRGF0ZSIsIm5vdyIsIm1lc3NhZ2VIVE1MIiwiaW5zZXJ0QWRqYWNlbnRIVE1MIiwibWVzc2FnZUVsZW1lbnQiLCJzdGFydFRpbWVyIiwiY29udGFpbmVyIiwiY3JlYXRlRWxlbWVudCIsImFwcGVuZENoaWxkIiwiaXRlbSIsInRpbWVyQ2lyY2xlIiwicmFkaXVzIiwiY2lyY3VtZmVyZW5jZSIsIk1hdGgiLCJQSSIsInN0eWxlIiwic3Ryb2tlRGFzaGFycmF5Iiwic3Ryb2tlRGFzaG9mZnNldCIsInByb2dyZXNzIiwiaW50ZXJ2YWwiLCJzZXRJbnRlcnZhbCIsImNsZWFySW50ZXJ2YWwiLCJoaWRlTWVzc2FnZSIsIm9mZnNldCJdLCJzb3VyY2VSb290IjoiIn0=