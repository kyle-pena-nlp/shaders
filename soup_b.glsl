/*
Mouse tracking / interactivity
*/




void mainImage( out vec4 fragColor, in vec2 fragCoord )
{    
    vec4 m2_mouse  = texelFetch(iChannel1, M2_POS_ADDR, 0);
    vec4 m1_mouse  = texelFetch(iChannel1, M1_POS_ADDR, 0);
    vec4 m0_mouse  = texelFetch(iChannel1, M0_POS_ADDR, 0);

    
    bool draw = (iMouse.z > 0.) && (m2_mouse.z > 0.) && (m1_mouse.z > 0.);

    if (ivec2(fragCoord) == M2_POS_ADDR) {
        //vec2 prevMouse = texelFetch(iChannel1, MOUSE_POS_ADDR, 0).xy;
        fragColor = vec4(iMouse.xyz, 0.);
    }
    
    if (ivec2(fragCoord) == M1_POS_ADDR) {
        fragColor = m2_mouse;
    }
    
    if (ivec2(fragCoord) == M0_POS_ADDR) {
        fragColor = m1_mouse;
    }

    
    if (ivec2(fragCoord) == DRAW_ADDR) {
        fragColor = draw ? vec4(1.) : vec4(0.);
    }
}