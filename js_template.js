"use strict";

const external_code = `#SHADER_PLACEHOLDER#`;

class ImportError extends Error {}

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
    addresses: {
        position: null,
        resolution: null,
        mouse: null,
        time: null
    }
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

function init() {
    createCanvasIfNotExists();
    createWebGLContextIfNotExists();
    createShaderProgram();
    configureWebGLContext();
    app.status = "ready";
}

function createShader(gl, shaderCode, shaderType) {
  
  var shader = gl.createShader(shaderType);
  gl.shaderSource(shader, shaderCode);
  gl.compileShader(shader);

  var message = gl.getShaderInfoLog(shader);
  if (message.length > 0) {
    /* message may be an error or a warning */
    throw message; 
  }

  return shader;
}

function createShaderProgram() {
    if (app.program) {
        return;
    }
    const gl = app.gl;
    const vertexShader = createShader(gl, getVertexShaderCode(), gl.VERTEX_SHADER);
    const fragmentShader = createShader(gl, getFragmentShaderCode(), gl.FRAGMENT_SHADER);
    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    app.program = program;
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
        app.capture = app.canvas.toDataURL('image/png', 1).substring(22);
      }
      else if (app.mode == "animate") {
         requestAnimationFrame(app.render);
      }

    }

    app.render = render;
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


function getFragmentShaderCode() {
  // build the fragment shader by prepending / postpending other code
  const fs = `#version 300 es

    precision mediump float;

    out vec4 myOutputColor;

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
