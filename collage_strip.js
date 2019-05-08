'use strict';
function process_request() {
    /* const xhr = createCORSRequest('GET', document.forms[0].dropbox_link.value,);
    if (!xhr) {
        throw new Error('CORS not supported');
    }
    xhr.onload = function () {
        var responseText = xhr.responseText;
        console.log(responseText);
        // process the response.
    };
    xhr.onreadystatechange = function () {
        console.log(xhr.status.toString() + '-' + xhr.readyState.toString())
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log(xhr.responseText);
        }
    };
    xhr.onerror = function () {
        console.log('There was an error!');
    };
    */
    const new_zip = new JSZip();
    JSZipUtils.getBinaryContent(document.forms[0].dropbox_link.value, function (err, data) {
        if (err) {
            throw err; // or handle err
        }
        new_zip.loadAsync(data)
            .then(function (zip) {
                // you now have every files contained in the loaded zip
                new_zip.file("hello.txt").async("string"); // a promise of "Hello World\n"
            });
    });
    return;
}

function createCORSRequest(method, url) {
    var xhr = new XMLHttpRequest();
    console.log(xhr);
    xhr.onreadystatechange = function () {
        console.log(xhr.status.toString() + '-' + xhr.readyState.toString())
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log(xhr.responseText);
        }
    };
    xhr.withCredentials = true;
    xhr.open(method, url);
    xhr.send();
    if ("withCredentials" in xhr) {

        // Check if the XMLHttpRequest object has a "withCredentials" property.
        // "withCredentials" only exists on XMLHTTPRequest2 objects.
        xhr.open(method, url, true);

    } else if (typeof XDomainRequest != "undefined") {

        // Otherwise, check if XDomainRequest.
        // XDomainRequest only exists in IE, and is IE's way of making CORS requests.
        xhr = new XDomainRequest();
        xhr.open(method, url);

    } else {

        // Otherwise, CORS is not supported by the browser.
        xhr = null;

    }
    return xhr;
}

