
#define VORONOI_EXPONENT 2.0
#define VORONOI_RANDOMNESS 1.0
#define VORONOI_ANGLE 3.14159/4.
#define VORONOI_UV_SCALE 10.

const ivec2 MOUSE_DOWN_ADDR = ivec2(2);
const ivec2 DRAW_ADDR       = ivec2(3);
const ivec2 M2_POS_ADDR = ivec2(4);
const ivec2 M1_POS_ADDR = ivec2(5);
const ivec2 M0_POS_ADDR = ivec2(6);

// per IQ: https://www.iquilezles.org/www/articles/distfunctions2d/distfunctions2d.htm
float segmentDist(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p-a, ba = b-a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    return length( pa - ba*h );
}

// https://thebookofshaders.com/12/
vec2 random2f( vec2 p ) {
    return fract(
        sin(
            vec2(
                dot(p,vec2(127.1,311.7)),
                dot(p,vec2(269.5,183.3)))
        )*(43758.5453)
    );
}

float veronoi_metric( in vec2 r, float exponent, float angle ) {
    // manhattan
    //return dot(abs(r), vec2(1.));
    // euclidean
    //return dot(r,r);
    return dot(pow(abs(r),vec2(exponent)), 0.01+abs(vec2(cos(angle), sin(angle))));
}


vec4 voronoi_f1_colors( in vec2 x, float randomness, float power, float angle )
{
    vec2 p = floor( x );
    vec2  f = fract( x );

    float res = 8.0;
    vec3 res_col = vec3(0.);
    for( int j=-1; j<=1; j++ )
    for( int i=-1; i<=1; i++ )
    {
        vec2 b = vec2( i, j );
        vec2 point = random2f( vec2(p + b) );
        vec2  r = vec2( b ) - f + randomness*point;
        float d = veronoi_metric( r, power, angle);
        vec3 col = vec3(point,1.);

        res_col = (d < res) ? col : res_col;
        res = min( res, d );
    }
    return vec4(res_col, sqrt( res ));
}

float divergence_calculation(vec2 va, vec2 vb, vec2 vc, vec2 vd, vec2 ve, vec2 vf, vec2 vg, vec2 vh, vec2 vi) {

    float divergence = 
    dot(normalize(va), -0.707*vec2(-1,-1)) +
    dot(normalize(vb), -vec2(-1, 0)) +
    dot(normalize(vc), -0.707*vec2(-1, 1)) +
    dot(normalize(vd), -vec2( 0,-1)) +
    dot(normalize(ve), -vec2( 0, 0)) +
    dot(normalize(vf), -vec2( 0, 1)) +
    dot(normalize(vg), -0.707*vec2( 1,-1)) +
    dot(normalize(vh), -vec2( 1, 0)) +
    dot(normalize(vi), -0.707*vec2( 1, 1));
    
    return (divergence) / 1.;
}


vec2 get_mouse_perturbation_calcuation(in vec2 fragCoord, bool draw, vec2 m2, vec2 m1, vec2 m0) {
    

    // use some distance fields to calculate brush size
    float dist1 = segmentDist(fragCoord, m2, m1);
    float dist2 = segmentDist(fragCoord, m1, m0);
    float dist = min(dist1,dist2);
    vec2 mouse_v = m2-m1;
    bool brush = dist < 15.;
    bool moving = length(mouse_v) > 0.;
    
    // update the color - in the future this will be an IMPULSE
    float strength = (1./(dist+1.));    
    vec2 perturb = (draw && brush && moving) ? strength*mouse_v : vec2(0.);
    
    return perturb;
}

