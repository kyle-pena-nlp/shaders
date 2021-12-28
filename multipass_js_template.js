"use strict";

// stuff gets swapped into here
const common_code     = `#COMMON_CODE#`
const external_code = `#SHADER_PLACEHOLDER#`;
const external_code_A = `#SHADER_PLACEHOLDER_A#`;
const external_code_B = `#SHADER_PLACEHOLDER_B#`;
const external_code_C = `#SHADER_PLACEHOLDER_C#`;

class ImportError extends Error {}

// Some of this code is based off of: https://codepen.io/jbltx/pen/eYZwEja

const app = {
    mode: null, /* capture or animate */
    status : null, /* null or 'ready' */
    capture: null, /* base64 capture */
    render: null, /* capture or animation callback */
    canvas: null,
    gl: null,
    mouseX: 0,
    mouseY: 0,
    program: null,

    vertexArray: null,

    bufferAProgram: null,
    bufferBProgram: null,
    bufferCProgram: null,

    framebufferA : null,
    framebufferB : null,
    framebufferC : null,

    textureA: null,
    textureB: null,
    textureC: null
};

function resizeCanvasToWindow() {
    const canvas = app.canvas;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

function setMousePosition(e) {
    const canvas = app.canvas;
    const rect = canvas.getBoundingClientRect();
    app.mouseX = e.clientX - rect.left;
    app.mouseY = rect.height - (e.clientY - rect.top) - 1;  // bottom is 0 in WebGL
}

// create a canvas element the size of the screen, that also automatically resizes and updates mouse positions
function createCanvasIfNotExists() {

    // lazy create the canvas
    if (!app.canvas) {
        const canvas = document.createElement('canvas')
        canvas.setAttribute("id", "canvas")
        document.body.appendChild(canvas)
        app.canvas = canvas;
    }

    // size the canvas to the entire window
    resizeCanvasToWindow();

    window.addEventListener('resize', resizeCanvasToWindow);
    app.canvas.addEventListener('mousemove', setMousePosition);
}

function createWebGLContextIfNotExists() {
    // lazy load the web gl context
    if (!app.gl) {
        app.gl = app.canvas.getContext("webgl2");
    }
}

function configureVertexArray() {
  const gl = app.gl;
  app.vertexArray = gl.createVertexArray();
  gl.bindVertexArray(app.vertexArray);
  gl.bindVertexArray(null);
}

function init() {

    createCanvasIfNotExists();
    createWebGLContextIfNotExists();

    const gl = app.gl;

    // make the buffers
    app.bufferAProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("A"));
    app.bufferBProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("B"));
    app.bufferCProgram = createShaderProgram(getCommonShaderCode() + getBufferFragmentShaderCode("C"));
    app.program        = createShaderProgram(getCommonShaderCode() + getFragmentShaderCode());  
    
    // make the frame buffers (???)
    app.framebufferA = gl.createFramebuffer();
    app.framebufferB = gl.createFramebuffer();    
    app.framebufferC = gl.createFramebuffer();   
    
    // make the textures
    app.textureA = createTexture(gl, gl.canvas.width, gl.canvas.height);   
    app.textureB = createTexture(gl, gl.canvas.width, gl.canvas.height); 
    app.textureC = createTexture(gl, gl.canvas.width, gl.canvas.height);      

    // do a bunch of other stuff
    configureWebGLContext();

    app.status = "ready";
}

function createShaderProgram(fragmentShaderCode) {
    
  const vertexShader = createShader(getVertexShaderCode(), gl.VERTEX_SHADER);
  const fragmentShader = createShader(fragmentShaderCode, gl.FRAGMENT_SHADER);

  const gl = app.gl;
  const program = gl.createProgram();
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

function createTexture(w, h) 
{
    const gl = app.gl;
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

// TODO: create frame rendering API

function configureWebGLContext() {
    
    const gl = app.gl;    

    const program = app.program;

    // look up where the vertex data needs to go.
    const positionAttributeLocation = gl.getAttribLocation(program, "position");

    // look up uniform locations
    const resolutionLocation = gl.getUniformLocation(program, "iResolution");
    const mouseLocation      = gl.getUniformLocation(program, "iMouse");
    const timeLocation       = gl.getUniformLocation(program, "iTime");

    // Create a buffer to put three 2d clip space points in
    const positionBuffer = gl.createBuffer();

    // Bind it to ARRAY_BUFFER (think of it as ARRAY_BUFFER = positionBuffer)
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);

    // fill it with a 2 triangles that cover clipspace
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
    -1, -1,  // first triangle
     1, -1,
    -1,  1,
    -1,  1,  // second triangle
     1, -1,
     1,  1,
    ]), gl.STATIC_DRAW);

    let then = 0;
    let time = 0;
    
    function render(now) {

      let gl = app.gl;

      if (app.mode == "animate") {
        now *= 0.001;  // convert to seconds
        const elapsedTime = Math.min(now - then, 0.1);
        time += elapsedTime;
        then = now;
      }
      else if (app.mode == "capture") {
        time = now;
      }

      drawBuffer(app.bufferAProgram, time, frame);
      drawBuffer(app.bufferBProgram, time, frame);
      drawBuffer(app.bufferCProgram, time, frame);
  
      // Tell WebGL how to convert from clip space to pixels
      gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
  
      // Tell it to use our program (pair of shaders)
      gl.useProgram(program);
  
      // Turn on the attribute
      gl.enableVertexAttribArray(positionAttributeLocation);
  
      // Bind the position buffer.
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
  
      // Tell the attribute how to get data out of positionBuffer (ARRAY_BUFFER)
      gl.vertexAttribPointer(
          positionAttributeLocation,
          2,          // 2 components per iteration
          gl.FLOAT,   // the data is 32bit floats
          false,      // don't normalize the data
          0,          // 0 = move forward size * sizeof(type) each iteration to get the next position
          0,          // start at the beginning of the buffer
      );
  
      gl.uniform2f(resolutionLocation, gl.canvas.width, gl.canvas.height);
      gl.uniform2f(mouseLocation, app.mouseX, app.mouseY);
      gl.uniform1f(timeLocation, time);
  
      gl.drawArrays(
          gl.TRIANGLES,
          0,     // offset
          6,     // num vertices to process
      );

      if (app.mode == "capture") {
        // TODO: proper DPI tricks if DPI != 96 desired.
        app.capture = app.canvas.toDataURL('image/png', 1).substring(22);
      }
      else if (app.mode == "animate") {
         requestAnimationFrame(app.render);
      }

    }

    app.render = render;
}

function drawBuffer(program, time, frame) {

    const gl = app.gl;

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);

    // TODO: remove these lines? 
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    //gl.clearColor(0, 0, 0, 0);
    //gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    gl.useProgram(program);

    gl.uniform1f(gl.getUniformLocation(program, "iTime"), time);
    gl.uniform1i(gl.getUniformLocation(app.bufferAProgram, "iFrame"), frame);
    gl.uniform2f(gl.getUniformLocation(program, "iMouse"), app.mouseX, app.mouseY);
    gl.uniform3f(gl.getUniformLocation(program, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
    
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

function draw(time)
{
    frame = (frame + 1);
    time *= 0.001;

    const gl = app.gl;    
    
    if (resize(gl.canvas))
    {
        if (gl.canvas.width <= 0 || gl.canvas.width <= 0)
          return;
      
        gl.deleteTexture(app.textureA);
        gl.deleteTexture(app.textureB);
        gl.deleteTexture(app.textureC);

        app.textureA = createTexture(gl, gl.canvas.width, gl.canvas.height);   
        app.textureB = createTexture(gl, gl.canvas.width, gl.canvas.height);
        app.textureC = createTexture(gl, gl.canvas.width, gl.canvas.height);   
    }

    // Buffer A
    {
        gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, app.framebufferA);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, app.textureA, 0);

        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        gl.useProgram(bufferAProgram);
        gl.uniform1f(gl.getUniformLocation(app.bufferAProgram, "iTime"), time);
        gl.uniform1i(gl.getUniformLocation(app.bufferAProgram, "iFrame"), frame);
        gl.uniform3f(gl.getUniformLocation(app.bufferAProgram, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
      
        gl.bindVertexArray(vertexArray);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    // Buffer B
    {
        gl.bindFramebuffer(gl.FRAMEBUFFER, framebufferB);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, textureB, 0);

        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        gl.useProgram(bufferBProgram);
        gl.uniform3f(gl.getUniformLocation(bufferBProgram, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
        
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, textureA);
        gl.uniform1i(gl.getUniformLocation(bufferBProgram, "iChannel0"), 0);
      
        gl.bindVertexArray(vertexArray);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    // Image
    {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);

        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

        gl.useProgram(imageProgram);
        gl.uniform1f(gl.getUniformLocation(imageProgram, "iTime"), time);
        gl.uniform3f(gl.getUniformLocation(imageProgram, "iResolution"), gl.canvas.width, gl.canvas.height, 1.0);
        
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, textureA);
        gl.uniform1i(gl.getUniformLocation(imageProgram, "iChannel0"), 0);
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, textureB);
        gl.uniform1i(gl.getUniformLocation(imageProgram, "iChannel1"), 1);
      
        gl.bindVertexArray(vertexArray);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }            
}

function getVertexShaderCode() {
    const vs = `#version 300 es

    // an attribute will receive data from a buffer
    in vec4 position;

    // all shaders have a main function
    void main() {

      // gl_Position is a special variable a vertex shader
      // is responsible for setting
      gl_Position = position;
    }`;
    return vs;
}


function getCommonShaderCode() {

  const fs = `#version 300 es

    precision mediump float;`

    +

    common

    +

    `void main() {
      mainImage(myOutputColor, gl_FragCoord.xy);
    }
  `;

  return fs;
}


function getBufferFragmentShaderCode(buffer) {

  const buffer_code = ({ "A": external_code_A, "B": external_code_B, "C": external_code_C })[buffer];

  const fs = `
    out vec4 myOutputColor;

    uniform sampler2D iChannel0;
    uniform sampler2D iChannel1;
    uniform sampler2D iChannel2;

    uniform vec2 iResolution;
    uniform vec2 iMouse;
    uniform float iTime;`

    

    +

    buffer_code

    +

    `void main() {
      mainImage(myOutputColor, gl_FragCoord.xy);
    }
  `;

  return fs;

}

function getFragmentShaderCode() {
  // build the fragment shader by prepending / postpending other code
  const fs = `
    out vec4 myOutputColor;

    uniform sampler2D iChannel0;
    uniform sampler2D iChannel1;
    uniform sampler2D iChannel2;    

    uniform vec2 iResolution;
    uniform vec2 iMouse;
    uniform float iTime;`

    

    +

    external_code

    +

    `void main() {
      mainImage(myOutputColor, gl_FragCoord.xy);
    }
  `;

  return fs;

}

function capture(time, x, y) {
    app.canvas.width = x;
    app.canvas.height = y;
    app.mode = "capture";
    app.render(time);
}

function animate() {
    resizeCanvasToWindow();
    app.mode = "animate";
    requestAnimationFrame(app.render);
}

function stop() {
    app.mode = "capture";
}


init();
animate();
