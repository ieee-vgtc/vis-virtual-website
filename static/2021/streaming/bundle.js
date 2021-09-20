(() => {
  // ieeevisdb.ts
  var IeeeVisDb = class {
    constructor() {
      this.initFirebase();
    }
    initFirebase() {
      firebase.initializeApp({
        apiKey: "AIzaSyCfFQ-eN52od55QBFZatFImgZgEDHK_P4E",
        authDomain: "ieeevis.firebaseapp.com",
        databaseURL: "https://ieeevis-default-rtdb.firebaseio.com",
        projectId: "ieeevis",
        storageBucket: "ieeevis.appspot.com",
        messagingSenderId: "542997735159",
        appId: "1:542997735159:web:6d9624111ec276a61fd5f2",
        measurementId: "G-SNC8VC6RFM"
      });
      firebase.analytics();
    }
    loadRoom(roomId2, onRoomUpdated) {
      this.roomRef = firebase.database().ref("rooms/" + roomId2);
      this.roomRef.on("value", (snapshot) => {
        onRoomUpdated(snapshot.val());
      });
    }
    loadSession(sessionId, onSessionUpdated) {
      this.sessionRef = firebase.database().ref("sessions/" + sessionId);
      this.sessionRef.on("value", (snapshot) => {
        onSessionUpdated(snapshot.val());
      });
    }
    set(path, value) {
      this.sessionRef?.child(path).set(value);
    }
    setRoom(path, value) {
      this.roomRef?.child(path).set(value);
    }
  };

  // youtubeplayer.ts
  var PlayerState;
  (function(PlayerState2) {
    PlayerState2[PlayerState2["UNSTARTED"] = -1] = "UNSTARTED";
    PlayerState2[PlayerState2["ENDED"] = 0] = "ENDED";
    PlayerState2[PlayerState2["PLAYING"] = 1] = "PLAYING";
    PlayerState2[PlayerState2["PAUSED"] = 2] = "PAUSED";
    PlayerState2[PlayerState2["BUFFERING"] = 3] = "BUFFERING";
    PlayerState2[PlayerState2["CUED"] = 5] = "CUED";
  })(PlayerState || (PlayerState = {}));

  // videoplayer.ts
  var IeeeVisVideoPlayer = class {
    constructor(elementId, getCurrentVideo, getCurrentVideoId, getCurrentVideoStatus) {
      this.elementId = elementId;
      this.getCurrentVideo = getCurrentVideo;
      this.getCurrentVideoId = getCurrentVideoId;
      this.getCurrentVideoStatus = getCurrentVideoStatus;
      this.audioContext = new AudioContext();
      this.width = 400;
      this.height = 300;
      this.youtubeApiReady = false;
      this.youtubePlayerLoaded = false;
      this.youtubePlayerReady = false;
      this.init();
    }
    onYouTubeIframeAPIReady() {
      this.youtubeApiReady = true;
    }
    updateVideo() {
      if (!this.getCurrentVideoId() || !this.youtubeApiReady) {
        return;
      }
      if (!this.youtubePlayerLoaded) {
        this.loadYoutubePlayer();
      } else {
        this.changeYoutubeVideo();
      }
    }
    setSize(width, height) {
      this.width = width;
      this.height = height;
      if (!this.player) {
        return;
      }
      this.player.setSize(width, height);
    }
    init() {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      const firstScriptTag = document.getElementsByTagName("script")[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
    onPlayerReady() {
      console.log("player ready", this.player);
      this.youtubePlayerReady = true;
      if (this.audioContext.state === "suspended") {
        this.player.mute();
      }
      this.player.playVideo();
    }
    onPlayerStateChange(state) {
      if (state.data === PlayerState.UNSTARTED) {
        this.player.seekTo(this.getCurrentStartTimeS() || 0, true);
      }
      if (state.data === PlayerState.PLAYING || state.data === PlayerState.BUFFERING) {
        const startTime = this.getCurrentStartTimeS() || 0;
        const currentTime = this.player.getCurrentTime();
        if (Math.abs(startTime - currentTime) > 5) {
          this.player.seekTo(startTime, true);
          console.log("lagging behind. seek.", this.getCurrentStartTimeS(), this.player.getCurrentTime());
        }
      }
    }
    loadYoutubePlayer() {
      this.youtubePlayerLoaded = true;
      this.player = new YT.Player(this.elementId, {
        width: this.width,
        height: this.height,
        videoId: this.getCurrentVideoId(),
        playerVars: {
          "playsinline": 1,
          "autoplay": 1,
          "controls": 1,
          "rel": 0,
          "modestbranding": 1,
          "mute": 0,
          start: this.getCurrentStartTimeS()
        },
        events: {
          "onReady": this.onPlayerReady.bind(this),
          "onStateChange": this.onPlayerStateChange.bind(this)
        }
      });
    }
    changeYoutubeVideo() {
      this.player.loadVideoById(this.getCurrentVideoId(), this.getCurrentStartTimeS());
      this.player.playVideo();
    }
    getCurrentStartTimeS() {
      if (!this.getCurrentVideo().live || !this.youtubePlayerReady) {
        const timeMs = new Date().getTime();
        const videoStartTimestampMs = this.getCurrentVideoStatus()?.videoStartTimestamp || 0;
        return Math.round((timeMs - videoStartTimestampMs) / 1e3);
      } else if (this.getCurrentVideo().live) {
        return this.player.getDuration();
      }
    }
  };

  // main.ts
  var _IeeeVisStream = class {
    constructor(ROOM_ID) {
      this.ROOM_ID = ROOM_ID;
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.PANEL_WIDTH_PERCENT = 40;
      this.CHAT_PADDING_LEFT_PX = 20;
      this.HORIZONTAL_PADDING = 30;
      this.currentPanelFocus = "none";
      this.db = new IeeeVisDb();
      this.player = new IeeeVisVideoPlayer(_IeeeVisStream.PLAYER_ELEMENT_ID, this.getCurrentStage.bind(this), this.getCurrentVideoId.bind(this), () => this.currentSession?.currentStatus);
      this.db.loadRoom(ROOM_ID, (room) => this.onRoomUpdated(room));
      this.loadGathertown();
      this.resize();
      window.addEventListener("resize", this.resize.bind(this));
      this.checkPanelFocus();
    }
    onYouTubeIframeAPIReady() {
      this.player.onYouTubeIframeAPIReady();
    }
    loadChat() {
      document.getElementById("discord-wrap").innerHTML = `
            <iframe
                id="discord-iframe"
                src="https://ieeevis-e.widgetbot.co/channels/884159773287805038/${this.currentSession.discord}"
            ></iframe>`;
    }
    loadSlido() {
      const frame = document.getElementById("slido-frame");
      frame.setAttribute("src", `https://app.sli.do/event/${this.currentSession.slido}`);
    }
    checkPanelFocus() {
      window.setInterval(() => {
        const lastFocus = this.currentPanelFocus;
        if (document.activeElement == document.getElementById("discord-iframe")) {
          this.currentPanelFocus = "chat";
        } else if (document.activeElement == document.getElementById("slido-frame")) {
          this.currentPanelFocus = "qa";
        } else {
          this.currentPanelFocus = "none";
        }
        if (lastFocus != this.currentPanelFocus) {
          this.resize();
        }
      }, 200);
    }
    loadGathertown() {
      const html = `<iframe title="gather town"
                              allow="camera;microphone"
                              id="gathertown-iframe"
                              src="https://gather.town/app/aDeS7vVGW5A2wuF5/vis21-tech2"></iframe>`;
      const gatherWrap = document.getElementById(_IeeeVisStream.GATHERTOWN_WRAPPER_ID);
      gatherWrap.innerHTML = html;
    }
    onRoomUpdated(room) {
      this.room = room;
      this.db.loadSession(room.currentSession, (session) => this.onSessionUpdated(room.currentSession, session));
    }
    onSessionUpdated(id, session) {
      if (this.room?.currentSession != id) {
        return;
      }
      const lastSession = this.currentSession ? {...this.currentSession} : void 0;
      const lastYtId = this.getCurrentVideoId();
      this.currentSession = session;
      document.getElementById("video-name").innerText = this.getCurrentStage()?.title || "";
      if (this.getCurrentVideoId() != lastYtId) {
        this.player.updateVideo();
      }
      if (this.currentSession.discord != lastSession?.discord) {
        this.loadChat();
      }
      if (this.currentSession.slido != lastSession?.slido) {
        this.loadSlido();
      }
      this.resize();
    }
    getCurrentStage() {
      return this.currentSession?.stages[this.currentSession?.currentStatus?.videoIndex];
    }
    getCurrentVideoId() {
      return this.getCurrentStage()?.youtubeId;
    }
    resize() {
      this.width = window.innerWidth;
      this.height = window.innerHeight - 15;
      const state = this.getCurrentStage()?.state;
      if (state === "SOCIALIZING") {
        document.getElementById("youtube-outer").style.display = "none";
        document.getElementById("gathertown-outer").style.display = "block";
      } else {
        document.getElementById("youtube-outer").style.display = "block";
        document.getElementById("gathertown-outer").style.display = "none";
      }
      const contentWidth = this.width * (100 - this.PANEL_WIDTH_PERCENT) / 100 - this.HORIZONTAL_PADDING;
      const mainContentHeight = this.height - _IeeeVisStream.HEADERS_HEIGHT;
      const contentWrap = document.getElementById(_IeeeVisStream.CONTENT_WRAPPER_ID);
      contentWrap.style.width = `${contentWidth}px`;
      this.player.setSize(contentWidth, mainContentHeight);
      const gatherFrame = document.getElementById("gathertown-iframe");
      gatherFrame.setAttribute("width", `${contentWidth}`);
      gatherFrame.setAttribute("height", `${mainContentHeight}`);
      const panelWidth = this.width * this.PANEL_WIDTH_PERCENT / 100 - this.CHAT_PADDING_LEFT_PX;
      const panelHeight = this.height - _IeeeVisStream.HEADERS_HEIGHT * 2;
      let qaHeightPercent = state === "QA" ? 60 : 40;
      if (this.currentPanelFocus === "qa") {
        qaHeightPercent = 66;
      } else if (this.currentPanelFocus === "chat") {
        qaHeightPercent = 33;
      }
      document.getElementById("sidepanel").style.width = `${panelWidth}px`;
      const slidoFrame = document.getElementById("slido-frame");
      const slidoHeight = qaHeightPercent / 100 * panelHeight + 100;
      if (slidoFrame) {
        slidoFrame.setAttribute("width", `${panelWidth}`);
        slidoFrame.style.height = `${slidoHeight}px`;
        document.getElementById("slido-wrap").style.height = `${slidoHeight - 100}px`;
      }
      const discordFrame = document.getElementById("discord-iframe");
      if (discordFrame) {
        discordFrame.setAttribute("width", `${panelWidth}`);
        discordFrame.style.height = `${(100 - qaHeightPercent) / 100 * panelHeight}px`;
        document.getElementById("discord-wrap").style.height = `${(100 - qaHeightPercent) / 100 * panelHeight}px`;
      }
    }
  };
  var IeeeVisStream = _IeeeVisStream;
  IeeeVisStream.PLAYER_ELEMENT_ID = "ytplayer";
  IeeeVisStream.CONTENT_WRAPPER_ID = "content";
  IeeeVisStream.GATHERTOWN_WRAPPER_ID = "gathertown";
  IeeeVisStream.HEADERS_HEIGHT = 40;
  var roomId = location.search.indexOf("room=") === -1 ? "" : location.search.substr(location.search.indexOf("room=") + "room=".length);
  if (roomId) {
    const stream = new IeeeVisStream(roomId);
    document.getElementById("wrapper").style.display = "flex";
    onYouTubeIframeAPIReady = () => {
      stream.onYouTubeIframeAPIReady();
    };
  } else {
    document.getElementById("param-error").style.display = "block";
  }
})();
//# sourceMappingURL=bundle.js.map
