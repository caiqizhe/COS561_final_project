//Predictor-------------------------------------
var prediction_dict = {"g":[{url:"https://www.google.com/", hit_count:1, miss_count:0}]};
var history_input = {};
var ignore_keywords = ["http://www.", "https://www."];
var mode = "full_mode";
var server_address = "http://54.167.38.140:8080";
chrome.runtime.onMessage.addListener(function setValue(request) {
  if(request.action == "setMode") {
    mode = request.resource;
    console.log(mode);
  }
  if(request.action == "getMode"){
    chrome.runtime.sendMessage({
      action: "sendMode",
      resource: mode
    });
  }
});
chrome.omnibox.onInputChanged.addListener(
  function(text, suggest) {

    chrome.tabs.query({active:true, highlighted: true, currentWindow: true}, function(tabs) {
       var id = tabs[0].id
      if(id in history_input) {
        while(history_input[id].length > 0 && text.length <= history_input[id][history_input[id].length - 1].length) {
          history_input[id].pop(history_input.length - 1);
        }
      } else {
        history_input[id] = [];
      }
      if(text.length > 0)
        history_input[id].push(text);
    });
    // Send predict header
    if(text in prediction_dict){
      var temp = {};
      temp['type'] = 'predict';
      temp['tabUrl'] = prediction_dict[text][0]['url'];
      temp['mode'] = mode;
      sendPostRequest(temp,'predict');

    }
    suggest_array = [];
    for (var i in prediction_dict[text]) {
      suggest_array.push({content: prediction_dict[text][i]["url"], description: prediction_dict[text][i]["url"]});
    }
    suggest(suggest_array);
  });

// This event is fired with the user accepts the input in the omnibox.
chrome.omnibox.onInputEntered.addListener(
  function(text,discomposition) {
    if(text.indexOf("http") != -1){
      chrome.tabs.update(null,{highlighted: true, active: true, url:text});
    } else {
      chrome.tabs.update(null,{highlighted: true, active: true, url: "http://" + text});
    }
});

function addPredictionItem(history_input, prediction_dict, tabUrl) {
  for (var i in history_input) {
    var ignore = false;
    for(var index in ignore_keywords) {
      if(ignore_keywords[index].indexOf(history_input[i]) != -1) {
        ignore = true;
        break;
      }
    }
    if(ignore)
      continue;
    var array = prediction_dict[history_input[i]];
    if(array == undefined) {
      prediction_dict[history_input[i]] = [];
      prediction_dict[history_input[i]].push({url:tabUrl, hit_count: 1, miss_count: 0});
      continue;
    }
    var find = false;
    for(var j in array) {
      if(array[j]["url"] == tabUrl) {
        find = true;
        array[j]["hit_count"] += 1;
      } else {
        array[j]["miss_count"] += 1;
      }
    }
    if(find == false) {
      array.push({url:tabUrl, hit_count: 1, miss_count: 0});
    } else {
      sortDscOrderArray(array, "hit_count", "miss_count");
    }
  }
}
//----------------------------------------------------------------------
// Resources structure:
// Key: url, Value: Key:dns-prefetch: [], prefetch: [], preconnect: []
//var resources = {};

// temporary storage:
// Key: url 
var tempStorage = {};


chrome.tabs.onUpdated.addListener(function(tabId , info, tab) {
    if (info.status == "complete") {
      var url = tab.url;
      if (url != undefined && url.indexOf("chrome://") == -1) {
 
        console.log("complete");
        console.log(tempStorage[tabId])
        for(var requestId in tempStorage[tabId]) {
          if(tempStorage[tabId][requestId]['endTimeStamp'] == undefined)
            delete tempStorage[tabId][requestId];
        }
        var temp = {};
        temp['resources'] = tempStorage[tabId];
        temp['type'] = 'analyze';
        temp['tabUrl'] = url;
        sendPostRequest(temp,'analyze');
        console.log(temp['resources']);
        if(tabId in history_input && history_input[tabId].length != 0) {
          addPredictionItem(history_input[tabId], prediction_dict, url);
          history_input[tabId] = [];
        }

      } else {
        console.log("URL undefined");
      }

    }
});


//Analyze web requests. Only fetch GET requests
chrome.webRequest.onBeforeRequest.addListener(function(details) {
  if(details.type == 'main_frame' && details.tabId != -1) {
       tempStorage[details.tabId] = {};
      return;
  }
  if(details.tabId != -1) {
    if(tempStorage[details.tabId] == undefined)
      tempStorage[details.tabId] = {};
    tempStorage[details.tabId][details.requestId] = details;
    tempStorage[details.tabId][details.requestId]["startTimeStamp"] = details.timeStamp;
    delete tempStorage[details.tabId][details.requestId]["timeStamp"];
  }
}, {urls: ["<all_urls>"]});

chrome.webRequest.onHeadersReceived.addListener(function(details){
  if(details.tabId != -1) {
    if(tempStorage[details.tabId][details.requestId] != undefined) {
      for(var i in details.responseHeaders){
        if(details.responseHeaders[i]["name"] == "Date")
          tempStorage[details.tabId][details.requestId]["Date"] = details.responseHeaders[i]["value"];
        if(details.responseHeaders[i]["name"] == "Expires")
          tempStorage[details.tabId][details.requestId]["Expires"] = details.responseHeaders[i]["value"];
      }
    }
  }
}, {urls: ["<all_urls>"]},["responseHeaders"]);


chrome.webRequest.onCompleted.addListener(function(details) {
   //console.log(details);
   if(details.type == "main_frame") {
    return;
  }

   if(details.tabId != -1) {
      if(tempStorage[details.tabId][details.requestId] != undefined) {
        tempStorage[details.tabId][details.requestId]["endTimeStamp"] = details.timeStamp;
      }
  }
}, {urls: ["<all_urls>"]});

function sendGetRequest(url) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET", url); // true for asynchronous 
  xmlHttp.send(null);
}

function sendPostRequest(params, type) {
    params = JSON.stringify(params);
    var http = new XMLHttpRequest();
    var url = server_address;
    http.open("POST", url);
    var milliseconds = (new Date).getTime();
    //Send the proper header information along with the request
    http.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    http.send(params);
}

function sortByDomains(storage, url) {
  domains = {};
  var parser = document.createElement('a');
  for(var i in storage[url]) {
    parser.href =  storage[url][i]["url"];
    domain = parser.protocol + '//' + parser.hostname;
    if(domain in domains) {
      domains[domain].push(storage[url][i]);
    } else {
      domains[domain] = [];
      domains[domain].push(storage[url][i]);
    }
  }
  return domains;
}

function sortDecOrderDictKey(dict, attribute) {
  return Object.keys(dict).sort(function(a,b){return dict[b][attribute]-dict[a][attribute]});
}

function sortAscOrderArray(array, attribute) {
  array.sort(function(a, b){
    return  a[attribute] - b[attribute];
  });
}
function sortDscOrderArray(array, hit_count, miss_count) {
  array.sort(function(a, b){
    return  -a[hit_count]/ float(a[hit_count] + a[miss_count]) + b[hit_count] / float(b[hit_count] + b[miss_count]);
  });
}
function getTopNItem(array, n = 10) {
  returnArray = [];
  for(var i = 0; i < n && i < array.length; i++)
    returnArray.push(array[i])
  return returnArray;
}
function addLinkHeader(resource, n = 10) {
    var link = {};
    link.name = "Link";
    link.value = "";
    for(var type in resource) {
      var urls = getTopNItem(resource[type]);
      for(var i in urls) {
        link.value += "<" + urls[i] + ">; rel=" + type + ', ';
      }
    }
    return link;
}
function startFetch(url) {
  //get analyze tab url.
  // fetch process
  var params = {};
  params.type = "fetch";
  params.tabUrl = url;
  params = JSON.stringify(params);
  sendPostRequest(params, 'fetch');
}