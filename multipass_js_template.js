"use strict";

// stuff gets swapped into here
const common_code     = `#COMMON_PLACEHOLDER#`
const external_code = `#SHADER_PLACEHOLDER#`;
const external_code_A = `#SHADER_PLACEHOLDER_A#`;
const external_code_B = `#SHADER_PLACEHOLDER_B#`;
const external_code_C = `#SHADER_PLACEHOLDER_C#`;

// Some of this code is based off of: https://codepen.io/jbltx/pen/eYZwEja

const app = {

    status : null, /* null (uninitialized), 'ready', 'animate', 'capture' */

    canvas: null, /* The canvas element */
    gl: null, /* Webgl2 context for the canvas */
    mode: null, /* capture or animate */
    capture: null, /* base64 capture */

    // mouse tracking
    mouseX: 0.0,
    mouseY: 0.0,
    mouseZ: 0.0,

    /* not sure about this one */
    vertexArray: null,

    /* programs */
    program: null,
    bufferAProgram: null,
    bufferBProgram: null,
    bufferCProgram: null,

    // frame buffers
    framebufferA : null,
    framebufferB : null,
    framebufferC : null,

    // textures
    textureA: null,
    textureB: null,
    textureC: null,

    /* Time stuff */
    frame: 0,
    time: 0,
    lastTime: 0
};


function init() {

  createCanvas();
  createWebGLContext();
  createVertexArray();
  createPrograms();
  createFrameBuffers();
  createNewTextures();

  app.status = "ready";
}

function render(now) {

  setTime(now);

  drawBuffer(app.bufferAProgram, app.framebufferA, app.textureA);
  drawBuffer(app.bufferBProgram, app.framebufferB, app.textureB);
  drawBuffer(app.bufferCProgram, app.framebufferC, app.textureC);
  drawShader(app.program);

  app.frame += 1;

  // if render was called in "capture" mode, dump the canvas to app.capture and don't request another frame
  if (app.mode == "capture") {
    app.capture = app.canvas.toDataURL('image/png', 1).substring(22);
  }
  // if render was called in "animate" mode, request another frame
  else if (app.mode == "animate") {
     requestAnimationFrame(render);
  }

}


function capture(time, x, y) {
  resizeCanvas(x,y);
  app.mode = "capture";
  render(time);
}

function animate() {
  app.mode = "animate";
  requestAnimationFrame(render);
}

function stop() {
  app.mode = "capture"; // todo: 'stopped' status?
}


function click_setMouseXY(e) {
    const canvas = app.canvas;
    const rect = canvas.getBoundingClientRect();
    app.mouseX = e.clientX - rect.left;
    app.mouseY = rect.height - (e.clientY - rect.top) - 1;  // bottom is 0 in WebGL
}

function touch_setMouseXY(e) {

  e.preventDefault();
  
  const canvas = app.canvas;
  const rect = canvas.getBoundingClientRect();
  
  // i'm reading that on android mobile the property is changedTouches
  let touch = null;
  if (e.touches) {
    touch = e.touches[0]
  }
  else if (e.changedTouches) {
    touch = e.changedTouches[0]
  }

  app.mouseX = touch.pageX - rect.left;
  app.mouseY = rect.height - (touch.pageY - rect.top) - 1;  // bottom is 0 in WebGL
}

function handle_mousedown(e) {
  e.preventDefault();
  app.mouseZ = 1.0;
}

function handle_mouseup(e) {
  e.preventDefault();
  app.mouseZ = 0.0;
}

function handle_touchstart(e) {
  e.preventDefault();
  app.mouseZ = 1.0;
}

function handle_touchend(e) {
  e.preventDefault();
  app.mouseZ = 0.0;
}

function createWebGLContext() {
  // lazy load the web gl context
  app.gl = app.canvas.getContext("webgl2");
}

// create a canvas element the size of the screen, that also automatically resizes and updates mouse positions
function createCanvas() {

    // lazy create the canvas
    const canvas = document.createElement('canvas');
    canvas.setAttribute("id", "canvas");
    document.body.appendChild(canvas);
    app.canvas = canvas;

    // make the canvas as big as the window
    resizeCanvas(window.innerWidth, window.innerHeight);

    // and if the window ever changes sizes, resize the canvas to match it
    window.addEventListener('resize', handleResize);

    // touchmove (tablets/phones) or mousemove...
    app.canvas.addEventListener('mousemove', click_setMouseXY);
    app.canvas.addEventListener('touchmove', touch_setMouseXY);

    // touchstart/end (tablets/phones) or mouseup/down
    app.canvas.addEventListener('mousedown', handle_mousedown);
    app.canvas.addEventListener('mouseup', handle_mouseup);
    app.canvas.addEventListener('touchstart', handle_touchstart);
    app.canvas.addEventListener('touchend', handle_touchend);
}

function handleResize() {
  resizeCanvas(window.innerWidth, window.innerHeight);
}

function resizeCanvas(x,y) {

    const canvas = app.canvas;

    if (!canvas) {
      return;
    }

    const dirty = (x != canvas.width) || (y != canvas.height);

    if (dirty) {
      canvas.width = x;
      canvas.height = y;
    }
  
    // if the canvas size changes, we have to recreate our multipass textures with the new dimensions
    const initialized = !!app.mode;
    const valid = (canvas.width >= 0 && canvas.height >= 0);

    if (dirty && valid && initialized) {
      createNewTextures();
    }
}


function createNewTextures() {

  const gl = app.gl;

  if (app.textureA) {
    gl.deleteTexture(app.textureA);
  }
  app.textureA = createTexture();   
  
  if (app.textureB) {
    gl.deleteTexture(app.textureB);
  }
  app.textureB = createTexture(); 

  if (app.textureC) {
    gl.deleteTexture(app.textureC);
  }
  app.textureC = createTexture();   

}

function createVertexArray() {
  const gl = app.gl;
  app.vertexArray = gl.createVertexArray();
  gl.bindVertexArray(app.vertexArray);
  gl.bindVertexArray(null);
}


function createPrograms() {
  app.bufferAProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("A"));
  app.bufferBProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("B"));
  app.bufferCProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("C"));
  app.program        = createShaderProgram(getCommonShaderCode() + getFragmentShaderCode());  
}

function createFrameBuffers() {
  const gl = app.gl;
  app.framebufferA = gl.createFramebuffer();
  app.framebufferB = gl.createFramebuffer();    
  app.framebufferC = gl.createFramebuffer();  
}

function createShaderProgram(fragmentShaderCode) {
  
  const gl = app.gl;

  const program = gl.createProgram();
  const vertexShader = createShader(getVertexShaderCode(), gl.VERTEX_SHADER);
  const fragmentShader = createShader(fragmentShaderCode, gl.FRAGMENT_SHADER);
  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);
  var success = gl.getProgramParameter(program, gl.LINK_STATUS);
  if (!success) {
      throw ("program filed to link:" + gl.getProgramInfoLog (program));
  }    
  return program;
}

function createShader(shaderCode, shaderType) {
  
  const gl = app.gl;

  var shader = gl.createShader(shaderType);
  gl.shaderSource(shader, shaderCode);
  gl.compileShader(shader);

  var message = gl.getShaderInfoLog(shader);
  if (message.length > 0) {
    /* message may be an error or a warning */
    //throw message; 
    throw "could not compile shader:" + gl.getShaderInfoLog(shader);
  }

  return shader;
}

function createTexture() 
{
    const gl = app.gl;
    const w = gl.canvas.width;
    const h = gl.canvas.height;

    //var ext = gl.getExtension('OES_texture_float');
    //ext = gl.getExtension("EXT_color_buffer_float");
    
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 
                                   0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.bindTexture(gl.TEXTURE_2D, null);
    return texture;
}

function drawShader(program) {

  const gl = app.gl;
  const time = app.time;

  gl.bindFramebuffer(gl.FRAMEBUFFER, null);

  // TODO: remove these lines? 
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
  //gl.clearColor(0, 0, 0, 0);
  //gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  gl.useProgram(program);

  gl.uniform1f(gl.getUniformLocation(program, "iTime"), time);
  gl.uniform3f(gl.getUniformLocation(program, "iMouse"), app.mouseX, app.mouseY, app.mouseZ);
  gl.uniform3f(gl.getUniformLocation(program, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
  gl.uniform1i(gl.getUniformLocation(program, "iFrame"), app.frame);    

  // bind channel 0
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, app.textureA);
  gl.uniform1i(gl.getUniformLocation(program, "iChannel0"), 0);

  // bind channel 1
  gl.activeTexture(gl.TEXTURE1);
  gl.bindTexture(gl.TEXTURE_2D, app.textureB);
  gl.uniform1i(gl.getUniformLocation(program, "iChannel1"), 1);

  // bind channel 2
  gl.activeTexture(gl.TEXTURE2);
  gl.bindTexture(gl.TEXTURE_2D, app.textureC);
  gl.uniform1i(gl.getUniformLocation(program, "iChannel2"), 2);

  gl.bindVertexArray(app.vertexArray);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
}

function drawBuffer(program, frameBuffer, texture) {

    const gl = app.gl;
    const time = app.time;

    gl.bindFramebuffer(gl.FRAMEBUFFER, frameBuffer);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);

    // TODO: remove these lines? 
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    //gl.clearColor(0, 0, 0, 0); // this line doesn't cause an error
    //gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);


    gl.useProgram(program);

    gl.uniform1f(gl.getUniformLocation(program, "iTime"), time);
    gl.uniform3f(gl.getUniformLocation(program, "iMouse"), app.mouseX, app.mouseY, app.mouseZ);
    gl.uniform3f(gl.getUniformLocation(program, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
    gl.uniform1i(gl.getUniformLocation(program, "iFrame"), app.frame);    

    /*
    // bind channel 0
    if (texture != app.textureA) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, app.textureA);
      gl.uniform1i(gl.getUniformLocation(program, "iChannel0"), 0);
    }


    // bind channel 1
    if (texture != app.textureB) {
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, app.textureB);
      gl.uniform1i(gl.getUniformLocation(program, "iChannel1"), 1);
    }

  
    // bind channel 2
    if (texture != app.textureC) {
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, app.textureC);
      gl.uniform1i(gl.getUniformLocation(program, "iChannel2"), 2);
    }

    */

    gl.bindVertexArray(app.vertexArray);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    
}

function setTime(now) {
  // if render was called in "animate" mode, add the elapsed item to current time
  if (app.mode == "animate") {
    now *= 0.001;  // convert to seconds
    const elapsedTime = Math.min(now - app.lastTime, 0.1);
    app.time += elapsedTime;
    app.lastTime = now;
  }
  // if render was called in "capture" mode, the requested time ("now") is the time we want
  else if (app.mode == "capture") {
    app.time = now;
  }
}

function getVertexShaderCode() {
  const vertexPlane = `#version 300 es  
    void main()
    {
      float x = float((gl_VertexID & 1) << 2);
      float y = float((gl_VertexID & 2) << 1);
      gl_Position = vec4(x - 1.0, y - 1.0, 0, 1);
    }
  `;
  return vertexPlane;
}


function getCommonShaderCode() {

  const fs = `#version 300 es

    precision mediump float;
`

    +

    common_code;

  return fs;
}


function getBufferFragmentShaderCode(buffer) {

  const buffer_code = ({ "A": external_code_A, "B": external_code_B, "C": external_code_C })[buffer];

  const fs = `
    layout(location = 0) out vec4 myOutputColor;

    uniform sampler2D iChannel0;
    uniform sampler2D iChannel1;
    uniform sampler2D iChannel2;
    uniform sampler2D iChannel3;

    uniform vec3 iResolution;
    uniform vec3 iMouse;
    uniform float iTime;
    uniform int iFrame;
    `

    

    +

    buffer_code

    +

    `
    
    void main() {
      mainImage(myOutputColor, gl_FragCoord.xy);
    }
  `;

  return fs;

}

function getFragmentShaderCode() {
  // build the fragment shader by prepending / postpending other code
  const fs = `
    layout(location = 0) out vec4 myOutputColor;

    uniform sampler2D iChannel0;
    uniform sampler2D iChannel1;
    uniform sampler2D iChannel2; 
    uniform sampler2D iChannel3;    

    uniform vec3 iResolution;
    uniform vec3 iMouse;
    uniform float iTime;
    uniform int iFrame;
    `

    

    +

    external_code

    +

    `
    
    void main() {
      mainImage(myOutputColor, gl_FragCoord.xy);
    }
  `;

  return fs;

}



init();
animate();