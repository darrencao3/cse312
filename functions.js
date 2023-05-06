// Establish a WebSocket connection with the server
welcome()

const socket = new WebSocket('ws://' + window.location.host + '/websocket');

let webRTCConnection;

// Allow users to send messages by pressing enter instead of clicking the Send button
document.addEventListener("keypress", function (event) {
    if (event.code === "Enter") {
        sendMessage();
    }
});

// Read the comment the user is sending to chat and send it to the server over the WebSocket as a JSON string
function sendMessage() {
    const chatBox = document.getElementById("chat-comment");
    const comment = chatBox.value;
    chatBox.value = "";
    chatBox.focus();
    if (comment !== "") {
        socket.send(JSON.stringify({'messageType': 'chatMessage', 'comment': comment}));
    }
}

// Renders a new chat message to the page
function addMessage(chatMessage) {
    let chat = document.getElementById('chat');
    chat.innerHTML += "<b>" + chatMessage['username'] + "</b>: " + chatMessage["comment"] + "<br/>";
}

// called when the page loads to get the chat_history
function get_chat_history() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const messages = JSON.parse(this.response);
            for (const message of messages) {
                addMessage(message);
            }
        }
    };
    request.open("GET", "/chat-history");
    request.send();
}

// Called whenever data is received from the server over the WebSocket connection
socket.onmessage = function (ws_message) {
    const message = JSON.parse(ws_message.data);
    const messageType = message.messageType

    switch (messageType) {
        case 'chatMessage':
            addMessage(message);
            break;
        case 'webRTC-offer':
            webRTCConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
            webRTCConnection.createAnswer().then(answer => {
                webRTCConnection.setLocalDescription(answer);
                socket.send(JSON.stringify({'messageType': 'webRTC-answer', 'answer': answer}));
            });
            break;
        case 'webRTC-answer':
            webRTCConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
            break;
        case 'webRTC-candidate':
            webRTCConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
            break;
        default:
            console.log("received an invalid WS messageType");
    }
}

function startVideo() {
    const constraints = {video: true, audio: true};
    navigator.mediaDevices.getUserMedia(constraints).then((myStream) => {
        const elem = document.getElementById("myVideo");
        elem.srcObject = myStream;

        // Use Google's public STUN server
        const iceConfig = {
            'iceServers': [{'url': 'stun:stun2.1.google.com:19302'}]
        };

        // create a WebRTC connection object
        webRTCConnection = new RTCPeerConnection(iceConfig);

        // add your local stream to the connection
        webRTCConnection.addStream(myStream);

        // when a remote stream is added, display it on the page
        webRTCConnection.onaddstream = function (data) {
            const remoteVideo = document.getElementById('otherVideo');
            remoteVideo.srcObject = data.stream;
        };

        // called when an ice candidate needs to be sent to the peer
        webRTCConnection.onicecandidate = function (data) {
            if(data.candidate) {
                socket.send(JSON.stringify({'messageType': 'webRTC-candidate', 'candidate': data.candidate}));
            }
        };
    })
}


function connectWebRTC() {
    // create and send an offer
    webRTCConnection.createOffer().then(webRTCOffer => {
        socket.send(JSON.stringify({'messageType': 'webRTC-offer', 'offer': webRTCOffer}));
        webRTCConnection.setLocalDescription(webRTCOffer);
    });

}

function welcome() {
    document.getElementById("paragraph").innerHTML += "<br/>This text was added by JavaScript 😀"
    /*
    document.cookie = "count=1; max-age=3600"
    document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: 1</h1>"
    */

    let cookies = document.cookie.split(";")

    console.log(cookies.length)
    if (cookies.length === 0) {
        document.cookie = "count=1; max-age=3600"
        document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: 1</h1>"
    } else {
        for (let i = 0; i < cookies.length; i++) {
            let temp = cookies[i].split("=");
            let temp2 = temp[0].replace(/\s+/g, '')
            if (temp2 === "token") {
                console.log("this shouldn't happen")
            }
            else if (temp2 === "count") {
                if (isNaN(parseInt(temp[1]))) {
                    document.cookie = "count=1; max-age=3600"
                    document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: 1</h1>"
                } else {
                    let temp3 = (parseInt(temp[1]) + 1)
                    document.cookie = "count=" + temp3 + "; max-age=3600"
                    document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: " + temp3 + "</h1>"
                }
            } else {
                document.cookie = "=;expires=Sat, 29 Apr 2023 00:00:0 GMT;path=/";
            }
        }
        if (cookies.length === 1) {
            if (cookies[0].split("=")[0] === "token") {
                document.cookie = "count=1; max-age=3600"
                document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: 1</h1>"
            }
            if (cookies[0] === "") {
                document.cookie = "count=1; max-age=3600"
                document.getElementById("paragraph").innerHTML += "<h1>Number of page visits: 1</h1>"
            }
        }
    }

    get_chat_history()

    // use this line to start your video without having to click a button. Helpful for debugging
    // startVideo();
}

// hw4
function openSU() {
  document.getElementById("signupform").style.display = "block";
}

function closeSU() {
  document.getElementById("signupform").style.display = "none";
  document.getElementById("userSU").value = "";
  document.getElementById("passSU").value = "";
}

function openL() {
  document.getElementById("loginform").style.display = "block";
}

function closeL() {
  document.getElementById("loginform").style.display = "none";
  document.getElementById("loginSU").value = "";
  document.getElementById("loginSU").value = "";
}

document.getElementById("signupform").addEventListener("submit", (e) => {
    e.preventDefault();
    let user = document.getElementById("userSU").value
    let pass = document.getElementById("passSU").value

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/signup", true);
    xhr.send(JSON.stringify({"user": user, "pass": pass}))

    document.getElementById("signupform").style.display = "none";
    document.getElementById("userSU").value = "";
    document.getElementById("passSU").value = "";
})

document.getElementById("loginform").addEventListener("submit", (e) => {
    e.preventDefault();
    let user = document.getElementById("userL").value
    let pass = document.getElementById("passL").value
    let token = Math.random().toString(36).substr(2) + Math.random().toString(36).substr(2) + Math.random().toString(36).substr(2);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/login", true);
    xhr.send(JSON.stringify({"user": user, "pass": pass, "token": token}))

    document.getElementById("loginform").style.display = "none";
    document.getElementById("userL").value = "";
    document.getElementById("passL").value = "";
})