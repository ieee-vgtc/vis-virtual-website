(() => {
  // ieeevisdb.ts
  var IeeeVisDb = class {
    constructor(SESSION_ID, onData) {
      this.SESSION_ID = SESSION_ID;
      this.onData = onData;
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
    loadData() {
      this.sessionRef = firebase.database().ref("sessions/" + this.SESSION_ID);
      this.sessionRef.on("value", (snapshot) => {
        this.onData(snapshot.val());
      });
    }
    set(path, value) {
      this.sessionRef.child(path).set(value);
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
        this.player.seekTo(this.getCurrentStartTimeS(), true);
      }
      if (state.data === PlayerState.PLAYING || state.data === PlayerState.BUFFERING) {
        const startTime = this.getCurrentStartTimeS();
        const currentTime = this.player.getCurrentTime();
        if (Math.abs(startTime - currentTime) > 5) {
          this.player.seekTo(this.getCurrentStartTimeS(), true);
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
      if (this.getCurrentVideo().type === "prerecorded" || !this.youtubePlayerReady) {
        const timeMs = new Date().getTime();
        const videoStartTimestampMs = this.getCurrentVideoStatus()?.videoStartTimestamp;
        return Math.round((timeMs - videoStartTimestampMs) / 1e3);
      } else if (this.getCurrentVideo().type === "live") {
        return this.player.getDuration();
      }
    }
  };

  // main.ts
  var _IeeeVisStream = class {
    constructor() {
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.CHAT_WIDTH_PERCENT = 40;
      this.CHAT_PADDING_LEFT_PX = 20;
      this.currentPanelTab = "discord";
      this.db = new IeeeVisDb(_IeeeVisStream.SESSION_ID, this.onData.bind(this));
      this.player = new IeeeVisVideoPlayer(_IeeeVisStream.PLAYER_ELEMENT_ID, this.getCurrentVideo.bind(this), this.getCurrentVideoId.bind(this), () => this.data?.currentStatus);
      this.db.loadData();
      this.loadGathertown();
      this.initPanelTabs();
      this.resize();
      window.addEventListener("resize", this.resize.bind(this));
    }
    onYouTubeIframeAPIReady() {
      this.player.onYouTubeIframeAPIReady();
    }
    loadChat() {
      const discordUrl = `https://titanembeds.com/embed/851543399982170163?defaultchannel=${this.data.discord}`;
      const rocketUrl = `https://chat.wushernet.com/channel/${this.data.rocketchat}?layout=embedded`;
      const url = location.hash.indexOf("discord") === -1 ? rocketUrl : discordUrl;
      const html = `<iframe src="${url}" id="discord-iframe" frameborder="0"></iframe>`;
      document.getElementById("discord-wrap").innerHTML += html;
    }
    loadSlido() {
      const frame = document.getElementById("slido-frame");
      frame.setAttribute("src", `https://app.sli.do/event/${this.data.slido}`);
    }
    loadGathertown() {
      const html = `<iframe title="gather town"
                              allow="camera;microphone"
                              id="gathertown-iframe"
                              src="https://gather.town/app/aDeS7vVGW5A2wuF5/vis21-tech2"></iframe>`;
      const gatherWrap = document.getElementById(_IeeeVisStream.GATHERTOWN_WRAPPER_ID);
      gatherWrap.innerHTML = html;
    }
    onData(session) {
      const initializing = this.data === null || this.data === void 0;
      const lastYtId = this.getCurrentVideoId();
      this.data = session;
      document.getElementById("track-title").innerText = this.data.name;
      document.getElementById("video-name").innerText = this.getCurrentVideo()?.title;
      if (this.getCurrentVideoId() != lastYtId) {
        this.player.updateVideo();
      }
      if (initializing) {
        this.loadChat();
        this.loadSlido();
      }
      this.resize();
    }
    getCurrentVideo() {
      return this.data?.videos[this.data?.currentStatus?.videoIndex];
    }
    getCurrentVideoId() {
      return this.getCurrentVideo()?.youtubeId;
    }
    initPanelTabs() {
      const getToggle = (tabName) => () => {
        console.log(tabName);
        this.currentPanelTab = tabName;
        this.updatePanelTabs();
      };
      document.getElementById("discord-tab-link").onclick = getToggle("discord");
      document.getElementById("slido-tab-link").onclick = getToggle("slido");
    }
    updatePanelTabs() {
      document.getElementById("discord-tab-link").className = "";
      document.getElementById("slido-tab-link").className = "";
      document.getElementById(`${this.currentPanelTab}-tab-link`).className = "active";
      document.getElementById("discord-wrap").className = "";
      document.getElementById("slido-wrap").className = "";
      document.getElementById(`${this.currentPanelTab}-wrap`).className = "active";
    }
    resize() {
      this.width = window.innerWidth;
      this.height = window.innerHeight - 65;
      const state = this.getCurrentVideo()?.state;
      const gathertownHeightPercent = state === "SOCIALIZING" ? 65 : 35;
      const playerWidth = this.width * (100 - this.CHAT_WIDTH_PERCENT) / 100;
      const playerHeight = (this.height - _IeeeVisStream.HEADERS_HEIGHT * 2) * (100 - gathertownHeightPercent) / 100;
      this.player.setSize(playerWidth, playerHeight);
      const gatherFrame = document.getElementById("gathertown-iframe");
      const gatherWidth = this.width * (100 - this.CHAT_WIDTH_PERCENT) / 100;
      const gatherHeight = (this.height - _IeeeVisStream.HEADERS_HEIGHT * 2) * gathertownHeightPercent / 100;
      gatherFrame.setAttribute("width", `${gatherWidth}`);
      gatherFrame.setAttribute("height", `${gatherHeight}`);
      const contentWrap = document.getElementById(_IeeeVisStream.CONTENT_WRAPPER_ID);
      contentWrap.style.width = `${gatherWidth}px`;
      this.currentPanelTab = state === "QA" ? "slido" : "discord";
      this.updatePanelTabs();
      const slidoFrame = document.getElementById("slido-frame");
      if (slidoFrame) {
        slidoFrame.setAttribute("width", `${this.width * this.CHAT_WIDTH_PERCENT / 100 - this.CHAT_PADDING_LEFT_PX}`);
        slidoFrame.setAttribute("height", `${this.height - _IeeeVisStream.HEADERS_HEIGHT}`);
      }
      const discordFrame = document.getElementById("discord-iframe");
      if (discordFrame) {
        discordFrame.setAttribute("width", `${this.width * this.CHAT_WIDTH_PERCENT / 100 - this.CHAT_PADDING_LEFT_PX}`);
        discordFrame.setAttribute("height", `${this.height - _IeeeVisStream.HEADERS_HEIGHT}`);
      }
    }
  };
  var IeeeVisStream = _IeeeVisStream;
  IeeeVisStream.PLAYER_ELEMENT_ID = "ytplayer";
  IeeeVisStream.CONTENT_WRAPPER_ID = "content";
  IeeeVisStream.GATHERTOWN_WRAPPER_ID = "gathertown";
  IeeeVisStream.SESSION_ID = location.search.substr(location.search.indexOf("session=") + "session=".length);
  IeeeVisStream.HEADERS_HEIGHT = 40;
  var stream = new IeeeVisStream();
  onYouTubeIframeAPIReady = () => {
    stream.onYouTubeIframeAPIReady();
  };
})();
//# sourceMappingURL=bundle.js.map
