window.onload = function(){
	chrome.runtime.sendMessage({
    action: "getMode",
    });
    chrome.runtime.onMessage.addListener(function setValue(request) {
		if(request.action == "sendMode"){
			document.getElementById("mode").innerText = request.resource;
			var select = document.getElementById("select");
			for(var i, j = 0; i = select.options[j]; j++) {
			    if(i.value == request.resource) {
			        select.selectedIndex = j;
			        break;
			    }
			}
		}
  	});
  	var select = document.getElementById("select");
	select.addEventListener("change",function(){
		var select = document.getElementById("select");
		
		document.getElementById("mode").innerText = select.options[select.selectedIndex].value;
	    chrome.runtime.sendMessage({
	    action: "setMode",
	    resource: select.options[select.selectedIndex].value
	    });
	});

}
