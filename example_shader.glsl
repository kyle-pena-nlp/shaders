
const int AA = 1;

const float EPS = 1e-8;
const float PI = 3.1415962;

#define LOOP_TIME 10.
const float RATE_1 = 2. * PI / LOOP_TIME;
const float PHASE_1 = PI / 2.;
const float NUM_CELLS = 10.;


mat2 noise2d_rotator = mat2(-0.8, 0.6, 0.6, 0.8);


// { "loop": ("-1.", 0.10), "blue": ("0.", 0.23), "red": ("1.", 0.23), "green":("2.", 0.22), "teal": ("3.", 0.22) }
#define COLOR_MODE 1.


#define BOUNCE 1

// { "kalm": ("0.", 0.80), "jittery": ("1.", 0.20) }
#define JITTERY 1.

#define VIGNETTE 1.

// { "glitched": ("1.", 0.30), "notglitched": ("0.", 0.70) }
#define STATIC 0.

// { "spinner": ("10.",0.15), "glass": ("1.", 0.15), "smooth": ("0.0", 0.70) }
#define FRACTURE 0.

// { "liney": ("1.", 0.20), "noliney": ("0.", 0.80) }
#define SCANLINE 0.

// { "ghost": ("1", 0.20), "plain": ("0", 0.80) }
#define TRAILS 0

// { "barrel": ("1", 0.20), "nobarrel": ("0", 0.80) }
#define BARREL 0

// { "I": ("0", 0.20), "II": ("1", 0.20), "III": ("2", 0.20), "IV": ("3", 0.20), "V": ("4", 0.20) }
#define POLYNOMIAL 4

#define SHAPES 20

const int MAX_ITER = SHAPES;

struct Poly3 {
    float A;
    float B;
    float C;
    float D;
};

struct Z {
    float real;
    float imag;
};



Z _multiplier(float time) {
    if (POLYNOMIAL == 0) {
        return Z(-1.+0.9*sin(RATE_1*time),-0.1+0.9*cos(RATE_1*time));
    }
    else if (POLYNOMIAL == 1) {
        return Z(-1.+0.9*sin(RATE_1*time),-0.1+0.9*cos(RATE_1*time));
    }    
    else if (POLYNOMIAL == 2) {
        return Z(-2.+0.1*sin(RATE_1*time),-2.+0.1*cos(RATE_1*time));
    }        
    else if (POLYNOMIAL == 3) {
        return Z(-1.+0.9*sin(RATE_1*time),-0.1+0.9*cos(RATE_1*time));
    }        
    else if (POLYNOMIAL == 4) {
        return Z(-1.1 + 0.1*sin(RATE_1*time),-1.1);
    }
    else if (POLYNOMIAL == 5) {
         return Z(0.0,-1.+0.9*sin(RATE_1*time));
    }
}

Poly3 getPoly(float time) {
    Poly3 p = Poly3(0., 0., 0., 0.);
    if (POLYNOMIAL == 0) {
        p = Poly3(1.,0.,0.,-1.);
    }
    else if (POLYNOMIAL == 1) {
        p = Poly3(0.,2.,0.,-2.);
    }
    else if (POLYNOMIAL == 2) {
        p = Poly3(3.,0.0,0.0,-3.);
    }
    else if (POLYNOMIAL == 3) {
        p = Poly3(7.,-0.5,-0.1,-1.);
    }
    else if (POLYNOMIAL == 4) {
        p = Poly3(1.,0.,0.,-1.);
    }
    
    float bounce =  (BOUNCE == 1) ? sin(RATE_1 * time) : 0.0;

    return Poly3(p.A, p.B, p.C, p.D + bounce);
}


float HUE_SHIFT_FRAC(float time) {
    if (COLOR_MODE == -1.) {
        return time / LOOP_TIME;
    }
    else if (COLOR_MODE == 0.) {
        return 0.0;
    }
    else if (COLOR_MODE == 1.) {
        return 0.24;
    }
    else if (COLOR_MODE == 2.) {
        return 0.6;
    }
    else if (COLOR_MODE == 3.) {
        return 0.85;
    }
    else {
        return 0.0;
    }
}



// from https://www.shadertoy.com/view/MsjXRt
// todo: my own implementation
vec3 HueShift (in vec3 Color, in float Shift)
{
    vec3 P = vec3(0.55735)*dot(vec3(0.55735),Color);
    
    vec3 U = Color-P;
    
    vec3 V = cross(vec3(0.55735),U);    

    Color = U*cos(Shift*6.2832) + V*sin(Shift*6.2832) + P;
    
    return Color;
}




Z add(Z a, Z b, Z c, Z d) {
    return Z(a.real + b.real + c.real + d.real, a.imag + b.imag + c.imag + d.imag);
}

Z add(Z a, Z b, Z c) {
    return Z(a.real + b.real + c.real, a.imag + b.imag + c.imag);
}

Z add(Z a, Z b) {
    return Z(a.real + b.real, a.imag + b.imag);
}

Z power(Z a, int exponent) {
    float r = pow(length(vec2(a.real, a.imag)), float(exponent));
    float cis = float(exponent) * atan(a.imag, a.real);
    return Z(r * cos(cis), r * sin(cis));  
}

Z conj(Z a) {
    return Z(a.real, -a.imag);
}

Z mult(float x, Z z) {
    return Z(x * z.real, x * z.imag);
}

Z mult(Z a, Z b) {
    return Z(a.real * b.real - a.imag * b.imag, a.real * b.imag + a.imag * b.real);
}

Z div(Z a, Z b) {
    
    Z numerator = mult(a, conj(b));
    float denom = mult(b,conj(b)).real;
    denom = denom == 0. ? 1. : denom;
    return mult(1./denom, numerator);
}




float fx(float x, Poly3 poly) {
    return poly.A*x*x*x + poly.B*x*x + poly.C*x + poly.D;
}

Z fz(Z z, Poly3 poly) {
    return add(mult(poly.A, power(z, 3)), mult(poly.B, power(z, 2)), mult(poly.C, power(z, 1)), Z(poly.D,0.)); 
}


Z dfdx(Z z, Poly3 poly) {
    return add(mult(3.*poly.A, power(z, 2)), mult(2.*poly.B, z), Z(poly.C,0.));
}

// TODO: handle divide by zero without branches or additive smoothing
Z next(Z z, Poly3 poly, Z multiplier) {
    return add(z, mult(multiplier,div(fz(z, poly), dfdx(z, poly))));
}

struct Result {
    int iterations;
    Z zero;
    float success;
    float d;
};

Result newtown_raphson(Z z, Poly3 poly, Z multiplier) {
    for (int i = 0; i < MAX_ITER; i++) {
        float d = z.real*z.real + z.imag*z.imag;
        if (d < EPS) {
            return Result(i, z, 1., d);
        }
        z = next(z, poly, multiplier);
    }
    float d =  z.real*z.real + z.imag*z.imag;
    return Result(MAX_ITER, z, 0., d);
}


vec3 render(in vec2 fragCoord, float time ) {
    // Normalized pixel coordinates (from 0 to 1)

    // AA accumulation
    vec3 tot = vec3(0.);
    
    // accumulation for finite differences
    // (I'm computing the gradient *while* doing AA)
    float dFdX  = 0.;
    float dFdY  = 0.;

    for (int i = -AA; i <= AA; i++) {
        for (int j = -AA; j <= AA; j++) {

            vec2 uv = ((fragCoord+((1.)/(2.*float(AA)))*vec2(i,j))/iResolution.xx);
            uv -= 0.5 * (iResolution.xy/iResolution.xx);

            Z z = Z(uv.x, uv.y);
            
            Z a = _multiplier(time);
            Result result = newtown_raphson(z, getPoly(time), a);

            float shade = clamp(float(result.iterations) / float(10), 0., 1.);
            
            dFdX += float(i) * shade;
            dFdY += float(j) * shade;

            // Time varying pixel color
            vec3 color = shade * shade * shade * shade * 0.5*(1.+clamp(vec3(result.zero.real, result.zero.imag, 1.), -1., 1.));
            
            tot += 0.15*(HueShift(color, HUE_SHIFT_FRAC(time)));
        }
    }

    tot /= float(AA * AA);
    
    
    // compute lighting using normal
    //tot *= dot(normalize(vec3(dFdX,dFdY,1.)), LIGHT_DIR());


    // Output to screen
    return tot;
}

// from IQ @ https://www.shadertoy.com/view/XdXGW8
vec2 grad2( ivec2 z )  // replace this anything that returns a random vector
{
    // 2D to 1D  (feel free to replace by some other)
    int n = z.x+z.y*11111;

    // Hugo Elias hash (feel free to replace by another one)
    n = (n<<13)^n;
    n = (n*(n*n*15731+789221)+1376312589)>>16;

    // Perlin style vectors
    n &= 7;
    vec2 gr = vec2(n&1,n>>1)*2.0-1.0;
    return ( n>=6 ) ? vec2(0.0,gr.x) : 
           ( n>=4 ) ? vec2(gr.x,0.0) :
                              gr;                             
}

float noise2_octave(in vec2 p, float intensity) 
{
     ivec2 i = ivec2(floor( p ));
     vec2 f =       fract( p );
	
	vec2 u = f*f*(3.0-2.0*f); // feel free to replace by a quintic smoothstep instead

    return mix( mix( dot( intensity*grad2( i+ivec2(0,0) ), f-vec2(0.0,0.0) ), 
                     dot( intensity*grad2( i+ivec2(1,0) ), f-vec2(1.0,0.0) ), u.x),
                mix( dot( intensity*grad2( i+ivec2(0,1) ), f-vec2(0.0,1.0) ), 
                     dot( intensity*grad2( i+ivec2(1,1) ), f-vec2(1.0,1.0) ), u.x), u.y);
}


// from IQ @ https://www.shadertoy.com/view/XdXGW8
float noise2( in vec2 p, int octaves, float intensity )
{
    float f = 0.;
    for (int i = 0; i < octaves; i++) {
        float coef = pow(2., -float(i + 1));
        f += coef*noise2_octave(p,intensity); 
        p = p*noise2d_rotator*2.01;
    }
    //f = 0.5 + 0.5*f;
    return f;
}

float fbm2( in vec2 x, int octaves, in float H )
{    
    float G = exp2(-H);
    float f = 1.0;
    float a = 1.0;
    float t = 0.0;
    for( int i=0; i<octaves; i++ )
    {
        t += a*noise2(f*x, 1, 1.);
        f *= 2.01;
        a *= G;
    }
    return t;
}

// https://www.iquilezles.org/www/articles/warp/warp.htm
vec2 distort2(in vec2 u, int iters, float scale, float intensity, float time) {
    vec2 p = vec2(u);
    p = vec2(
            fbm2(u+vec2(0.0,0.0),1,1.),
            fbm2(u+vec2(5.2,1.3),1,1.));
    for (int i = 0; i < iters-1; i++) 
    {
        p = vec2(
            fbm2(u + scale*p+vec2(1.7,9.2),1,1.),
            fbm2(u + scale*p+vec2(8.3,2.8),1,1.));
            
        p += vec2(time);
    }
    return u+intensity*p;
}

vec2 getJitter(float time)
{
    return 0.3*(distort2(vec2(time), 5, 1., 1., 0.) - vec2(time)); 
}

// this jitter implementatoin blends two jitters with 100% of A at t=0.0 and 100% of B at t=LOOP_TIME
// The blends are offset by t = -LOOP_TIME, that way, you have seemless looping of length LOOP_TIME
vec2 jitter(in vec2 fragCoord, float time) {
    vec2 jitter1 = getJitter(mod(time,LOOP_TIME));
    vec2 jitter2 =  getJitter(mod(time,LOOP_TIME) - LOOP_TIME);  
    vec2 jitter = mix(jitter1, jitter2, mod(time/LOOP_TIME,1.));
    return 500.*jitter;
}

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

struct Voronoi {
    vec3 col;
    float res;
    vec2 ij;
};

Voronoi voronoi_f1_colors( in vec2 x, float randomness, float power, float angle )
{
    vec2 p = floor( x );
    vec2  f = fract( x );

    float res = 8.0;
    vec3 res_col = vec3(0.);
    ivec2 ij = ivec2(0);
    
    for( int j=-1; j<=1; j++ )
    for( int i=-1; i<=1; i++ )
    {
        vec2 b = vec2( i, j );
        vec2 point = random2f( vec2(p + b) );
        vec2  r = vec2( b ) - f + randomness*point;
        float d = veronoi_metric( r, power, angle);
        vec3 col = vec3(point,1.);

        ij = (d < res) ? ivec2(i,j) : ij;
        res_col = (d < res) ? col : res_col;
        res = min( res, d );
        
    }
    
    return Voronoi(res_col, res, vec2(ij));
    //return vec4(res_col, sqrt( res ));
}

vec3 barrelize(vec2 fragCoord) {
    float a = -0.5;
    vec2 uv = 2.*(fragCoord.xy / iResolution.xy) - 1.;
    float ru = dot(uv,uv);
    vec2 uvd = uv * (1. - a * ru);
    vec2 coord = iResolution.xy*(uvd + 1.)/2.;
    float mask = clamp(coord, 0., 1.) == coord ? 1. : 0.;
    return vec3(coord, mask);
    //float rd = ru*(1. + a * ru);
    //float alpha = atan(uv.y, uv.x);
    //vec2 uvd = (vec2(rd * cos(alpha), rd * sin(alpha)) + 1.)/2.;
    //return uvd * iResolution.xy;
}


vec3 renderMainImage(in vec2 fragCoord, float time )
{


    vec2 oFragCoord = fragCoord;
    
    if (BARREL == 1) {
        vec3 barrel = barrelize(fragCoord);
        fragCoord = barrel.xy;
    }
    
    vec2 jitter_amt = jitter(fragCoord, time);
    fragCoord += JITTERY * jitter_amt;  
    
    vec2 uv = fragCoord.xy / iResolution.xx;    
    
    Voronoi voronoi = Voronoi(vec3(0.),0.,vec2(0));
    float voronoi_amt = 0.;
    vec2 renderFragCoord = fragCoord;
    if (FRACTURE > 0.) {
        voronoi = voronoi_f1_colors( NUM_CELLS*uv, 1., 2., PI/4. );
        voronoi_amt =  sin(5. * RATE_1 * time / LOOP_TIME);
        float a = mod(FRACTURE*(RATE_1 * time),2.*PI);
        vec2 center = (floor(NUM_CELLS*uv) + voronoi.ij + vec2(0.5)) / NUM_CELLS;
        mat2 spin = mat2(cos(a), -sin(a), sin(a), cos(a));
        renderFragCoord = iResolution.xx*((spin * (uv - center)) + center);// + voronoi_amt * 50. * voronoi.xy;
    }

    vec3 color = render(renderFragCoord, time);
    

    
    
    if (FRACTURE > 0.) {
        color = mix(voronoi.col.xyz, color, 1.-voronoi_amt/4.);
        color = color + voronoi_amt * 0.25 * dot(vec2(cos(RATE_1*time), sin(RATE_1*time)), (voronoi.col.xy));
        color = mix(color, vec3(1.), voronoi.res);
    }
    
    if (JITTERY == 1.) {
        //float fade = 10./length(jitter_amt);
        //color = fade * color; // "FLASH LOOKS DUMB" - bonk
    }
    

    if (SCANLINE == 1.) {
        float animate = 10.*time/LOOP_TIME;
        float y = 50.*(fragCoord.y/iResolution.y);
        float x = 2.*PI*(y + animate);
        float scanline = abs(sin(x));
        scanline = clamp(0.2 + scanline, 0., 1.);
        color = scanline * color;
    }

    
    if (VIGNETTE == 1.) {
        float d= length(oFragCoord.xy / iResolution.xy - vec2(0.5));
        float vignette = abs(1. - pow(d,1.));
        color = vignette * color;
    }
    
    
    if (STATIC == 1.) {
        vec2 uv = oFragCoord.xy / iResolution.xy;
        float static_mask = grad2(100*ivec2(5.*LOOP_TIME*time) + ivec2(vec2(100.,100.)*uv.xy)).x > 0.35 ? 1. : 0.;
        color = static_mask * mix(vec3(0.6,1.,0.6),color,0.9) + (1.-static_mask)*color;
    
    }
    
    
    
    //color = scanline_mask * mix(vec3(0.6,1.,0.6),color,0.1) + (1.-scanline_mask) * color;
    
    return color;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 color = renderMainImage(fragCoord, iTime);
    
    if (TRAILS > 0) {
        color = (1./float(1+TRAILS)) * color;
    }
    
    for (int i = 1; i <= TRAILS; i++) {
        vec3 trail = renderMainImage(fragCoord, iTime-0.35*(1./float(TRAILS))*float(i));
        //  HueShift(trail,0.1)
        // 0.1 * trail
        float coef = (1./float(1+TRAILS));//pow(2.,float(i));
        color += coef * vec3(length(trail)/pow(3.,0.5));
    }
    
    fragColor = vec4(color,1.);
    
}