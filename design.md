# Sora 2 AI Video Generation Platform - Design Style Guide

## Design Philosophy

### Visual Language
**Futuristic Minimalism with Technical Precision**: The design embodies the intersection of advanced AI technology and creative expression. Clean, geometric forms represent the algorithmic nature of AI, while fluid animations and subtle gradients reflect the creative potential of video generation. Every element should feel both cutting-edge and accessible.

### Color Palette
**Primary Colors**:
- Deep Space Blue (#0A0E1A) - Main background, conveying depth and technology
- Electric Cyan (#00D4FF) - Primary accent, representing AI energy and creativity
- Pure White (#FFFFFF) - Text and interface elements for maximum contrast
- Soft Gray (#F8F9FA) - Secondary backgrounds and subtle elements

**Accent Colors**:
- Neon Purple (#8B5CF6) - Progress indicators and active states
- Warm Orange (#FF6B35) - Warning states and generation activity
- Cool Green (#10B981) - Success states and completed actions

### Typography
**Primary Font**: "Inter" - Clean, modern sans-serif for maximum readability across all devices
**Display Font**: "JetBrains Mono" - Monospace font for code snippets and technical elements
**Heading Hierarchy**:
- H1: 3.5rem (56px) - Hero titles, bold weight
- H2: 2.5rem (40px) - Section headers, semibold weight
- H3: 1.875rem (30px) - Subsection headers, medium weight
- Body: 1rem (16px) - Regular text, normal weight

## Visual Effects & Styling

### Background Treatment
**Animated Particle Field**: Subtle, slow-moving particles using p5.js create a sense of digital atmosphere without being distracting. Particles should be semi-transparent cyan dots that pulse gently and respond to mouse movement.

### Interactive Elements
**Button Styling**:
- Primary buttons: Electric cyan background with white text, subtle glow effect on hover
- Secondary buttons: Transparent with cyan border, cyan background on hover
- Disabled states: Muted gray with reduced opacity

**Form Elements**:
- Input fields: Dark background with cyan focus border, smooth transitions
- Dropdowns: Minimal styling with subtle shadows and cyan accents
- Sliders: Custom cyan track with white handle, smooth animations

### Animation Library Usage

#### Anime.js Implementation
- **Page transitions**: Smooth fade-ins and slide animations for content sections
- **Button interactions**: Scale and glow effects on hover states
- **Progress indicators**: Smooth progress bar animations during video generation
- **Card animations**: Subtle lift and shadow effects on hover

#### p5.js Creative Coding
- **Background particle system**: Floating particles that respond to user interaction
- **Loading animations**: Dynamic visual feedback during AI processing
- **Data visualization**: Interactive charts showing generation statistics

#### ECharts.js Data Visualization
- **Usage analytics**: Clean, modern charts with cyan accent colors
- **Performance metrics**: Real-time visualization of platform statistics
- **Style consistency**: All charts use the established color palette

#### Shader Effects (shader-park)
- **Hero background**: Subtle liquid-metal displacement effect
- **Transition effects**: Smooth morphing between interface states
- **Visual depth**: Layered shader effects for premium feel

### Header & Navigation Effects
**Navigation Bar**:
- Glass morphism effect with subtle backdrop blur
- Smooth color transitions on scroll
- Active state indicators with cyan underline animation
- Responsive hamburger menu with smooth slide animations

**Logo Treatment**:
- Custom Sora 2 logo with subtle glow effect
- Animated on page load with scale and opacity transitions
- Consistent branding across all pages

### Scroll Motion Effects
**Reveal Animations**:
- Content sections fade in from bottom with 20px translation
- Staggered animations for card grids (100ms delays)
- Progress-triggered animations at 50% viewport entry
- Smooth easing curves (cubic-bezier(0.4, 0, 0.2, 1))

**Parallax Elements**:
- Subtle background movement (±5% translation)
- Applied only to decorative elements
- Maintains readability and accessibility

### Hover Effects
**Interactive Cards**:
- 3D tilt effect with perspective transformation
- Subtle shadow expansion and color shift
- Smooth scale transform (1.02x) on hover
- Cyan accent border appearance

**Image Elements**:
- Ken Burns effect (subtle zoom and pan)
- Overlay gradient appearance on hover
- Smooth opacity transitions for captions

**Navigation Elements**:
- Underline expansion animation
- Color morphing from white to cyan
- Smooth background color transitions

### Mobile Responsiveness
**Breakpoint Strategy**:
- Mobile: 320px - 768px (single column layout)
- Tablet: 768px - 1024px (two column layout)
- Desktop: 1024px+ (full multi-column layout)

**Touch Interactions**:
- Larger touch targets (44px minimum)
- Swipe gestures for gallery navigation
- Optimized particle effects for mobile performance

### Accessibility Considerations
**Color Contrast**: All text maintains 4.5:1 contrast ratio minimum
**Motion Sensitivity**: Reduced motion options for users with vestibular disorders
**Keyboard Navigation**: Full keyboard accessibility for all interactive elements
**Screen Reader Support**: Proper ARIA labels and semantic HTML structure

## Implementation Notes
- All animations respect user's motion preferences
- Fallback styles for JavaScript-disabled environments
- Progressive enhancement approach for advanced effects
- Performance optimization for smooth 60fps animations
- Consistent timing functions across all transitions