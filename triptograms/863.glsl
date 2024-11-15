
#define AA 1

#define LOOP_TIME 10.

// set programmatically at generaiton time
#define JITTER_SALT 863.0

const float EPS = 1e-12;
const float PI = 3.1415962;
const float e = 2.7182818284;


const float RATE_1 = 2. * PI / LOOP_TIME;
const float PHASE_1 = PI / 2.;
const float NUM_CELLS = 10.;


mat2 noise2d_rotator = mat2(-0.8, 0.6, 0.6, 0.8);


// { "loop": ("-1.", 0.10), "blue": ("0.", 0.23), "red": ("1.", 0.23), "green":("2.", 0.22), "teal": ("3.", 0.22) }
#define COLOR_MODE -1.

// undocumented value: 0: none
// { "twist": ("1", 0.33), "fritz": ("2", 0.33), "pulsar": ("3", 0.33) }
#define ANIMATION_STYLE 3

// { "kalm": ("0.", 0.80), "jittery": ("1.", 0.20) }
#define JITTERY 0.



// { "clearview": ("-1", 0.70), "tiles": ("0", 0.10), "gems": ("1", 0.10), "cubist": ("3", 0.10)}
#define FRACTURE_STYLE -1

#define SCANLINE 0.

#define TRAILS 0


// { "dragon": ("2.", 0.25), "tri": ("3.", 0.25), "quad": ("4.", 0.25),  "sept": ("6.", 0.25) }
#define LEADING_EXPONENT 3.

// { "stripeworld": ("-1.", 0.50), "spiralworld": ("1.", 0.50) }
#define LEADING_EXPONENT_SIGN -1.

// { "zoomout": ("-0.1", 0.25), "nakedeye": ("-1.",0.75)}
#define CONSTANT_REAL_TERM -1.

// { "polar": ("1",0.25), "cartesian": ("0",0.75) }
#define POLAR 0

// {  "regularness": ("0", 0.625), "velvet": ("1", 0.125), "neons": ("2", 0.125), "fantasy": ("3", 0.125) } 
#define SHADE_STYLE 2

// { "no": ("0", 0.50), "yes": ("1", 0.50) }
#define INVERT_COLORS 1

// { "yes": ("1", 0.30), "no": ("0", 0.70) }
#define FBM 1

#define VIGNETTE 0.

#define LEADING_TERM_COEF 5.

#define CONSTANT_IMAG_TERM 0.

#define LINEAR_TERM 0.0

#define QUADRATIC_TERM 0.0

#define SHAPES 10

#define Gx 0

const int MAX_ITER = SHAPES;

struct Poly3 {

    float A;
    float expA;

    float B;
    float expB;

    float C;
    float expC;

    float D;

    float E;
};

struct Z {
    float real;
    float imag;
};




Poly3 getPoly(float time) {

    float bounce =  (ANIMATION_STYLE == 1) ? sin(RATE_1 * time) : 0.0;

    //float constant_radius = CONSTANT_REAL_TERM + bounce;
    //float constant_real = constant_radius*cos(time);
    //float constant_imag = constant_radius*sin(time);

    return Poly3(LEADING_TERM_COEF, LEADING_EXPONENT_SIGN * LEADING_EXPONENT, QUADRATIC_TERM, LEADING_EXPONENT_SIGN * 2., LINEAR_TERM, LEADING_EXPONENT_SIGN, CONSTANT_REAL_TERM + bounce, CONSTANT_IMAG_TERM);
}



float _exp(float x) {
    return pow(e, x);
}


Z add(Z a, Z b, Z c, Z d, Z e, Z f) {
    return Z(a.real + b.real + c.real + d.real + e.real + f.real, a.imag + b.imag + c.imag + d.imag + e.imag + f.imag);
}

Z add(Z a, Z b, Z c, Z d, Z e) {
    return Z(a.real + b.real + c.real + d.real + e.real, a.imag + b.imag + c.imag + d.imag + e.imag);
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

Z power(Z a, float exponent) {
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

Z _ln(Z a) {
    return Z(length(vec2(a.real, a.imag)),  atan(a.imag, a.real));
}

Z _exp(Z a) {
    return mult(_exp(a.real), Z(cos(a.imag), sin(a.imag)) );
}

Z _cos(Z x) {
    float a = x.real;
    float b = x.imag;
    return Z(cos(a) * cosh(b), -1. * sin(a) * sinh(b));
}

Z _sin(Z x) {
    float a = x.real;
    float b = x.imag;
    return Z(sin(a) * cosh(b), -1. * cos(a)* sinh(b));
}

float _length(Z x) {
    return length(vec2(x.real, x.imag));
}

float _length_squared(Z x) {
    return x.real*x.real + x.imag*x.imag;
}

// Inner implementation - not to be called directly
Z _fz(Z z, Poly3 poly) {
    return add(mult(poly.A, power(z, poly.expA)), mult(poly.B, power(z, poly.expB)), mult(poly.C, power(z, poly.expC)), Z(poly.D,poly.E)); 
}

// Inner implementation - not to be called directly
Z _dfdx(Z z, Poly3 poly) {
    Z t1 = mult(poly.expA*poly.A, power(z, poly.expA-1.));
    Z t2 = mult(poly.expB*poly.B, power(z, poly.expB-1.));
    Z t3 = mult(poly.expC*poly.C, power(z, poly.expC-1.));
    return add(t1, t2, t3);
}

// F(z) = f(p(z)) = f(az^m-b)
Z fz(Z z, Poly3 poly) {
    Z a = _fz(z, poly);
    #if Gx == 0
        // identity
        return a;
    #elif Gx == 1
        // sin
        return _sin(a);
    #elif Gx == 2
        // exp
        return _exp(a);
    #elif Gx == 3
        // (1+f(x))/f(x)
        return div(add(Z(1.,0.), a), a);
    #else
        return 0.; // deliberate compiler error
    #endif
}

// F'(z) = F'(p(z))*p'(z)
Z dfdx(Z z, Poly3 poly) {
    Z a = _dfdx(z, poly);
    #if Gx == 0
        // chain rule applied to identity function
        return a;
    #elif Gx == 1
        // chain rule applied to sin
        return mult(_cos(_fz(z, poly)), a);
    #elif Gx == 2
        // chain rule applied to exp
        return mult(_exp(_fz(z, poly)), a);
    #elif Gx == 3
        // chain rule applied to (1+f(x))/f(x)
        Z numerator = a;
        Z denominator = power(_fz(z, poly), 2.); 
        return div(numerator,denominator);
    #else
        return 0.; // deliberate compiler error
    #endif 
}

// TODO: handle divide by zero without branches or additive smoothing
Z next(Z z, Poly3 poly, Z multiplier) {
    return add(z, mult(multiplier,div(fz(z, poly), dfdx(z, poly))));
}


Z _multiplier(float time) {

    Z multiplier = Z(1.,1.);

    if (ANIMATION_STYLE == 1) {
        multiplier = Z(-1.+0.9*sin(RATE_1*time),-0.1+0.9*cos(RATE_1*time));
    }
    else if (ANIMATION_STYLE == 2) {
        multiplier = div( Z(-1. + cos(RATE_1*time), 1. + sin(RATE_1*time) ), Z( 1. + sin(RATE_1*time) , -1. + cos(RATE_1*time) ) );
        //return Z(2., -3. + cos(RATE_1*time));
    }
    else if (ANIMATION_STYLE == 3 && LEADING_EXPONENT_SIGN == 1.) {
        multiplier = mult(Z(-0.1,-0.1), Z(sin(RATE_1*time), cos(RATE_1*time)));   
    }   
    else if (ANIMATION_STYLE == 3 && LEADING_EXPONENT_SIGN == -1.) {
        multiplier = mult(Z(-0.1,-0.1), Z(sin(RATE_1*time), cos(RATE_1*time))); 
        multiplier = add(multiplier, Z(-2.,0.));
    }
    
    return multiplier;
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


struct Result {
    int iterations;
    Z zero;
    float success;
    float d;
};



Result newtown_raphson(Z z, Poly3 poly, Z multiplier) {
    
    if (POLAR == 1) {
        z = div(Z(0.05,0.0),z);
    }
    
    #if SHADE_STYLE == 3
    float tot_d = 1.;
    #else
    float tot_d = 0.;
    #endif

    for (int i = 0; i < MAX_ITER; i++) {
        float d = z.real*z.real + z.imag*z.imag;
        
        #if SHADE_STYLE == 1
            tot_d = min(abs(atan(z.real,z.imag)), abs(atan(z.imag, z.real)));
        #elif SHADE_STYLE ==2
            //tot_d = max(tot_d, d);
            tot_d = (z.real + z.imag) / 2.;
        #elif SHADE_STYLE == 3
            tot_d *= (((z.real / z.imag)));
        #endif
        
        if (d < EPS) {
            return Result(i, z, 1., tot_d);
        }
        z = next(z, poly, multiplier);           
        
    }
    float d =  z.real*z.real + z.imag*z.imag;
    
    
    return Result(MAX_ITER, z, 0., tot_d);
}


vec3 render(in vec2 fragCoord, float time ) {
    // Normalized pixel coordinates (from 0 to 1)

    // AA accumulation
    vec3 tot = vec3(0.);

    vec2 uv = fragCoord.xy/iResolution.xx;
    
    uv -= 0.5 * (iResolution.xy/iResolution.xx);

    Z z = Z(uv.x, uv.y);
    
    Z a = _multiplier(time);
    Result result = newtown_raphson(z, getPoly(time), a);
    
    vec3 root_color = 0.5*(1.+clamp(vec3(result.zero.real, result.zero.imag, 1.), -1., 1.));

    #if SHADE_STYLE == 0
        float shade = clamp(float(result.iterations) / float(SHAPES), 0., 1.);                
    #elif SHADE_STYLE > 0
        float shade = clamp(result.d, 0., 1.);
    #else
        float shade = vec2(0.); // DELIBERATE COMPILER ERROR
    #endif

    // Time varying pixel color
    vec3 color = shade * shade * shade * root_color;

    tot += (0.15*9.)*(HueShift(color, HUE_SHIFT_FRAC(time)));
    
    #if INVERT_COLORS == 1
    tot = (1. - tot);
    #endif

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

vec2 getFBM(in vec2 uv, float time) {
    float UV_SCALE = 4./iResolution.x;
    float STRENGTH = (1./8.)*iResolution.x;
    return STRENGTH*(distort2(vec2(UV_SCALE*uv + JITTER_SALT + time), 2, 1., 1., 0.) - vec2(UV_SCALE*uv + JITTER_SALT + time));
}

vec2 fbm(in vec2 fragCoord, float time) {
    vec2 _fbm1 = getFBM(fragCoord, mod(time,LOOP_TIME));
    vec2 _fbm2 = getFBM(fragCoord, mod(time,LOOP_TIME) - LOOP_TIME);
    vec2 _fbm = mix(_fbm1, _fbm2, mod(time/LOOP_TIME,1.));
    return _fbm + fragCoord;
}

vec2 getJitter(float time)
{
    return 0.3*(distort2(vec2(JITTER_SALT + time), 5, 1., 1., 0.) - vec2(JITTER_SALT + time)); 
}

// this jitter implementatoin blends two jitters with 100% of A at t=0.0 and 100% of B at t=LOOP_TIME
// The blends are offset by t = -LOOP_TIME, that way, you have seemless looping of length LOOP_TIME
vec2 jitter(in vec2 fragCoord, float time) {
    vec2 jitter1 = getJitter(mod(time,LOOP_TIME));
    vec2 jitter2 =  getJitter(mod(time,LOOP_TIME) - LOOP_TIME);  
    vec2 jitter = mix(jitter1, jitter2, mod(time/LOOP_TIME,1.));
    return jitter;
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



vec3 renderMainImage(in vec2 fragCoord, float time )
{
    vec2 oFragCoord = fragCoord;
    
    vec2 jitter_amt = 500.*jitter(fragCoord, time);
    fragCoord += JITTERY * jitter_amt;  
    
    vec2 uv = fragCoord.xy / iResolution.xx;    
    
    Voronoi voronoi = Voronoi(vec3(0.),0.,vec2(0));
    float voronoi_amt = 0.;
    vec2 renderFragCoord = fragCoord;
    if (FRACTURE_STYLE >= 0) {
        voronoi = voronoi_f1_colors( NUM_CELLS*uv, float(FRACTURE_STYLE), 2. + 0.2*sin(RATE_1*time), PI/4. );
        voronoi_amt =  sin(5. * RATE_1 * time / LOOP_TIME);
        float a = mod(1.*(RATE_1 * time),2.*PI);
        vec2 center = (floor(NUM_CELLS*uv) + voronoi.ij + vec2(0.5)) / NUM_CELLS;
        mat2 spin = mat2(cos(a), -sin(a), sin(a), cos(a));
        renderFragCoord = iResolution.xx*((spin * (uv - center)) + center);// + voronoi_amt * 50. * voronoi.xy;
    }

    #if FBM > 0
    renderFragCoord = fbm(renderFragCoord, time);
    #endif

    vec3 color = render(renderFragCoord, time);
    
    if (FRACTURE_STYLE >= 0) {
        color = mix(voronoi.col.xyz, color, 1.-voronoi_amt/4.);
        color = color + voronoi_amt * 0.25 * dot(vec2(cos(RATE_1*time), sin(RATE_1*time)), (voronoi.col.xy));
        color = mix(color, vec3(1.), voronoi.res);
    }


    if (VIGNETTE == 1.) {
        float d= length(oFragCoord.xy / iResolution.xy - vec2(0.5));
        float vignette = abs(1. - pow(d,1.));
        color = vignette * color;
    }
    
    //color = scanline_mask * mix(vec3(0.6,1.,0.6),color,0.1) + (1.-scanline_mask) * color;
    
    return color;
}

vec3 _mainImage(in vec2 fragCoord) {
    vec3 color = renderMainImage(fragCoord, iTime);
    
    

    
    
    if (TRAILS > 0) {
        color = (1./float(1+TRAILS)) * color;
    }
    
    for (int i = 1; i <= TRAILS; i++) {
        vec3 trail = renderMainImage(fragCoord, iTime-0.35*(1./float(TRAILS))*float(i));
        float coef = (1./float(1+TRAILS));//pow(2.,float(i));
        color += coef * vec3(length(trail)/pow(3.,0.5));
    }
    
    return color;
    
}


void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    
    vec3 tot = vec3(0.0);
    
    #if AA > 0
    
    float AA_scale = 0.5;
    float coef = 0.;
    float denom = 0.0;
    float max_coef = float(1+2*AA);
    
    for (int i = -1*AA; i <= 1*AA; i++) {
        for (int j = -1*AA; j <= 1*AA; j++) {
            fragCoord += AA_scale * vec2(i,j);
            coef = max_coef - float(i+j);
            tot += coef * _mainImage(fragCoord);
            denom += coef;
        }
    }
    
    tot /= denom;
    
    #else
    
    tot = _mainImage(fragCoord);
    
    #endif
    

    
    fragColor = vec4(tot, 1.);
}