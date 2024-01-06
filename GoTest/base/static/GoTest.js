// Alert utils
const confirmButtonColor = "#1A6BE4"
const showMessage = (option, icon) => {
    return Swal.fire({
        title: option.title || null,
        text: option.text || null,
        icon: icon,
        confirmButtonColor: confirmButtonColor,
        ...option
    });
};

const showSuccessMessage = (option) => showMessage(option, "success");
const showErrorMessage = (option) => showMessage(option, "error");
const showWarningMessage = (option) => showMessage(option, "warning");
const showInfoMessage = (option) => showMessage(option, "info");
const showQuestionMessage = (option) => showMessage(option, "question");

// Tab utils
const getTabFromUrl = () => {
    const url = new URL(window.location.href);
    return url.searchParams.get("tab");
};
const changeTab = (activeTab) => {
    const activeTabId = `#${activeTab}`;
    const tabPaneId = $(activeTabId).data("bsTarget");
    $(activeTabId).addClass("active");
    $(tabPaneId).addClass("active show");
};
const updateUrl = (activeTab) => {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", activeTab);
    history.pushState("", "", url.toString());
};
const showActiveTab = (activeTab) => {
    changeTab(activeTab);
    updateUrl(activeTab);
};
const clickTab = (activeTab) => $(`#${activeTab}`).click(() => showActiveTab(activeTab));

// Ajax utils
const sendAjaxRequest = ({
    url,
    method,
    formData,
    dataType,
    headers,
    successMessage,
    errorMessage,
    successCallback,
    errorCallback,
    alwaysCallback
}) => {
    const handleSuccess = (data) => {
        showSuccessMessage({
            title: successMessage
        }).then((result) => {
            if (successCallback && typeof successCallback === 'function') {
                successCallback(result);
            }
        });
    };

    const handleError = (error) => {
        showErrorMessage({
            title: errorMessage,
            text: error && error.responseJSON ? error.responseJSON.result : null
        }).then((result) => {
            if (errorCallback && typeof errorCallback === 'function') {
                errorCallback(result);
            }
        });
    };

    const handleAlways = () => {
        if (alwaysCallback && typeof alwaysCallback === 'function') {
            alwaysCallback();
        }
    }

  const option = {
    type: method,
    url: url,
    success: handleSuccess,
    error: handleError,
    always: handleAlways
  }

  if (headers) {
    option.headers = headers;
  }

  if (dataType) {
    option.dataType = dataType;
  }

  if (formData) {
    option.data = formData;
  }

  $.ajax(option);
}

const submitFormWithAjax = ({
    formId,
    url,
    method,
    dataType,
    headers,
    successMessage,
    errorMessage,
    successCallback,
    errorCallback,
    alwaysCallback
}) => {
    const handleSubmit = (e) => {
        e.preventDefault();
        $(`${formId} button[type=submit]`).attr("disabled", true);

        const ajaxConfig = {
            url: url,
            method: method,
            formData: $(formId).serialize(),
            headers: headers || null,
            successMessage,
            errorMessage,
            successCallback: successCallback,
            errorCallback: errorCallback,
            alwaysCallback: alwaysCallback
        };

        if (dataType) {
            ajaxConfig.dataType = dataType;
        }
        // Call Ajax
        sendAjaxRequest(ajaxConfig);
    };
    console.log(formId)
    $(formId).submit(handleSubmit);
};

// Fetch API utils
const sendFetchRequest = ({
    url,
    method,
    formData,
    headers,
    successMessage,
    errorMessage,
    successCallback,
    errorCallback,
    alwaysCallback
}) => {
    const handleSuccess = (data) => {
        showSuccessMessage({
            title: successMessage
        }).then((result) => {
            if (successCallback && typeof successCallback === 'function') {
                successCallback(result);
            }
        });
    };

    const handleError = (error) => {
        showErrorMessage({
            title: errorMessage,
            text: error && error.responseJSON ? error.responseJSON.result : null
        }).then((result) => {
            if (errorCallback && typeof errorCallback === 'function') {
                errorCallback(result);
            }
        });
    };

  const handleAlways = () => {
      if (alwaysCallback && typeof alwaysCallback === 'function') {
          alwaysCallback();
      }
  };

  const option = {
    method: method,
  }

  if (headers) {
    option.headers = headers;
  }

  if (formData) {
    option.body = formData;
  }

  fetch(url, option)
    .then(response => {
        if (!response.ok) {
            throw new Error("Fail");
        }
        return response;
    })
    .then(handleSuccess)
    .catch(handleError)
    .finally(handleAlways);
};

// Submit Form utils with Fetch
const submitFormWithFetch = ({
    formId,
    url,
    method,
    headers,
    successMessage,
    errorMessage,
    successCallback,
    errorCallback,
    alwaysCallback
}) => {
    const handleSubmit = (e) => {
        e.preventDefault();
        $(`${formId} button[type=submit]`).attr("disabled", true);

        const fetchConfig = {
            url: url,
            body: $(formId).serialize(),
            method: method,
            headers: headers || null,
            successMessage,
            errorMessage,
            successCallback: successCallback,
            errorCallback: errorCallback,
            alwaysCallback: alwaysCallback
        };

        // Call Fetch API
        sendFetchRequest(fetchConfig);
    };

    $(formId).submit(handleSubmit);
};

const addCommasToNumber = (input) => {
    const [integerPart, decimalPart] = String(input).split('.');
    const formattedIntegerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    if (decimalPart === undefined) {
      return formattedIntegerPart;
    } else {
      return `${formattedIntegerPart}.${decimalPart}`;
    }
  };
