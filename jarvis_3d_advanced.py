# jarvis_3d_advanced.py
# 3D renderer WITHOUT bpy - uses PyVista and Matplotlib
from pathlib import Path
import json
import time
import numpy as np

# 3D rendering libraries (no bpy needed!)
PYVISTA_AVAILABLE = False
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
    print("✓ PyVista 3D renderer loaded")
except Exception:
    print("⚠ PyVista not available. Install with: pip install pyvista")

MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    MATPLOTLIB_AVAILABLE = True
    print("✓ Matplotlib 3D renderer loaded")
except Exception:
    print("⚠ Matplotlib not available. Install with: pip install matplotlib")

# ------------------ 3D data directory ------------------
DATA_DIR = Path("jarvis_full_data")
DATA_DIR.mkdir(exist_ok=True)
RENDERS_DIR = DATA_DIR / "renders"
RENDERS_DIR.mkdir(exist_ok=True)

# ------------------ Material database ------------------
MATERIAL_DATABASE = {
    "Titanium": {
        "metallic": 1.0,
        "roughness": 0.3,
        "color": [0.7, 0.7, 0.75],
        "reflectivity": 0.8,
        "description": "Strong, lightweight metal"
    },
    "Gold": {
        "metallic": 1.0,
        "roughness": 0.1,
        "color": [1.0, 0.84, 0.0],
        "reflectivity": 0.95,
        "description": "Precious yellow metal"
    },
    "Steel": {
        "metallic": 1.0,
        "roughness": 0.4,
        "color": [0.8, 0.8, 0.8],
        "reflectivity": 0.7,
        "description": "Durable iron alloy"
    },
    "Copper": {
        "metallic": 1.0,
        "roughness": 0.2,
        "color": [0.95, 0.64, 0.54],
        "reflectivity": 0.85,
        "description": "Reddish conductive metal"
    },
    "Glass": {
        "metallic": 0.0,
        "roughness": 0.0,
        "color": [0.9, 0.9, 1.0],
        "reflectivity": 0.3,
        "transmission": 0.9,
        "description": "Transparent material"
    },
    "Plastic": {
        "metallic": 0.0,
        "roughness": 0.6,
        "color": [0.2, 0.5, 0.8],
        "reflectivity": 0.2,
        "description": "Synthetic polymer"
    },
    "Wood": {
        "metallic": 0.0,
        "roughness": 0.8,
        "color": [0.6, 0.4, 0.2],
        "reflectivity": 0.1,
        "description": "Natural organic material"
    },
    "Diamond": {
        "metallic": 0.0,
        "roughness": 0.0,
        "color": [1.0, 1.0, 1.0],
        "reflectivity": 0.95,
        "transmission": 0.5,
        "description": "Crystal clear gemstone"
    }
}

# ------------------ 3D Mesh Generation ------------------
def create_cube_mesh(size=1.0):
    """Create cube vertices and faces"""
    s = size / 2
    vertices = np.array([
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # bottom
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]       # top
    ])
    
    faces = np.array([
        [0, 1, 2, 3], [4, 5, 6, 7],  # bottom, top
        [0, 1, 5, 4], [2, 3, 7, 6],  # front, back
        [0, 3, 7, 4], [1, 2, 6, 5]   # left, right
    ])
    
    return vertices, faces

def create_sphere_mesh(radius=1.0, resolution=20):
    """Create sphere vertices and faces"""
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    
    return x, y, z

def create_cylinder_mesh(radius=1.0, height=2.0, resolution=20):
    """Create cylinder vertices"""
    theta = np.linspace(0, 2 * np.pi, resolution)
    z = np.linspace(-height/2, height/2, 10)
    
    theta_grid, z_grid = np.meshgrid(theta, z)
    x = radius * np.cos(theta_grid)
    y = radius * np.sin(theta_grid)
    
    return x, y, z_grid

# ------------------ PyVista Renderer (BEST QUALITY) ------------------
def render_with_pyvista(material_name, shape, size):
    """
    High-quality 3D rendering with PyVista
    """
    if not PYVISTA_AVAILABLE:
        return None
    
    try:
        # Create plotter
        plotter = pv.Plotter(off_screen=True, window_size=[800, 800])
        
        # Create mesh based on shape
        if shape == "cube":
            mesh = pv.Cube(bounds=(-size/2, size/2, -size/2, size/2, -size/2, size/2))
        elif shape == "sphere":
            mesh = pv.Sphere(radius=size)
        elif shape == "cylinder":
            mesh = pv.Cylinder(radius=size/2, height=size*2)
        else:
            mesh = pv.Cube()
        
        # Apply material properties
        mat_props = MATERIAL_DATABASE.get(material_name, MATERIAL_DATABASE["Steel"])
        color = mat_props["color"]
        
        # Add mesh with material
        plotter.add_mesh(
            mesh,
            color=color,
            metallic=mat_props["metallic"],
            roughness=mat_props["roughness"],
            pbr=True,  # Physically Based Rendering
            smooth_shading=True
        )
        
        # Add lighting
        plotter.add_light(pv.Light(position=(10, 10, 10), intensity=0.8))
        plotter.add_light(pv.Light(position=(-10, -10, 10), intensity=0.4))
        
        # Set camera
        plotter.camera_position = [(size*3, size*3, size*3), (0, 0, 0), (0, 0, 1)]
        plotter.set_background('black')
        
        # Render and save
        output_path = RENDERS_DIR / f"{material_name}_{shape}_{int(time.time())}.png"
        plotter.screenshot(str(output_path))
        plotter.close()
        
        print(f"✓ PyVista render complete: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"PyVista render error: {e}")
        return None

# ------------------ Matplotlib Renderer (FALLBACK) ------------------
def render_with_matplotlib(material_name, shape, size):
    """
    Basic 3D rendering with Matplotlib (works everywhere!)
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    try:
        fig = plt.figure(figsize=(10, 10), facecolor='black')
        ax = fig.add_subplot(111, projection='3d', facecolor='black')
        
        # Get material properties
        mat_props = MATERIAL_DATABASE.get(material_name, MATERIAL_DATABASE["Steel"])
        color = mat_props["color"]
        alpha = 0.9 if mat_props.get("transmission", 0) < 0.5 else 0.6
        
        # Create and plot shape
        if shape == "cube":
            vertices, faces = create_cube_mesh(size)
            
            # Create 3D polygon collection
            poly_collection = []
            for face in faces:
                poly = [vertices[i] for i in face]
                poly_collection.append(poly)
            
            poly3d = Poly3DCollection(poly_collection, alpha=alpha, 
                                     facecolors=color, edgecolors='white', 
                                     linewidths=0.5)
            ax.add_collection3d(poly3d)
            
        elif shape == "sphere":
            x, y, z = create_sphere_mesh(size)
            ax.plot_surface(x, y, z, color=color, alpha=alpha, 
                          edgecolor='white', linewidth=0.1, antialiased=True)
            
        elif shape == "cylinder":
            x, y, z = create_cylinder_mesh(size/2, size*2)
            ax.plot_surface(x, y, z, color=color, alpha=alpha,
                          edgecolor='white', linewidth=0.1, antialiased=True)
        
        # Set labels and title
        ax.set_xlabel('X', color='white')
        ax.set_ylabel('Y', color='white')
        ax.set_zlabel('Z', color='white')
        ax.set_title(f'{material_name} {shape.capitalize()}', 
                    color='white', fontsize=16, fontweight='bold')
        
        # Set equal aspect ratio
        max_range = size * 1.5
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])
        
        # Style improvements
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=20, azim=45)
        
        # Save figure
        output_path = RENDERS_DIR / f"{material_name}_{shape}_{int(time.time())}.png"
        plt.savefig(output_path, dpi=150, facecolor='black', bbox_inches='tight')
        plt.close()
        
        print(f"✓ Matplotlib render complete: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Matplotlib render error: {e}")
        return None

# ------------------ Main Material Preview Function ------------------
def generate_material_preview(material_name, shape="cube", size=2.0):
    """
    Generate 3D material preview using best available renderer
    Priority: PyVista > Matplotlib > JSON
    """
    print(f"\n{'='*60}")
    print(f"🎨 3D Material Generation")
    print(f"{'='*60}")
    print(f"Material: {material_name}")
    print(f"Shape: {shape}")
    print(f"Size: {size}")
    
    # Validate material
    if material_name not in MATERIAL_DATABASE:
        print(f"⚠ Unknown material: {material_name}")
        print(f"Available materials: {', '.join(MATERIAL_DATABASE.keys())}")
        material_name = "Steel"
        print(f"Using default: {material_name}")
    
    mat_props = MATERIAL_DATABASE[material_name]
    print(f"Properties: {mat_props['description']}")
    print(f"  • Metallic: {mat_props['metallic']}")
    print(f"  • Roughness: {mat_props['roughness']}")
    print(f"  • Color: RGB{tuple(mat_props['color'])}")
    print(f"{'='*60}\n")
    
    # Try rendering with available methods
    result = None
    
    # Try PyVista first (best quality)
    if PYVISTA_AVAILABLE:
        print("🎯 Using PyVista renderer (High Quality)...")
        result = render_with_pyvista(material_name, shape, size)
        if result:
            return result
    
    # Fallback to Matplotlib
    if MATPLOTLIB_AVAILABLE:
        print("🎯 Using Matplotlib renderer (Good Quality)...")
        result = render_with_matplotlib(material_name, shape, size)
        if result:
            return result
    
    # Final fallback: JSON data
    print("⚠ No 3D renderer available. Generating JSON preview...")
    print("💡 Install PyVista for 3D rendering: pip install pyvista")
    
    preview_data = {
        "material": material_name,
        "shape": shape,
        "size": size,
        "properties": mat_props,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "vertices_count": get_estimated_vertices(shape),
        "renderer": "none"
    }
    
    preview_file = RENDERS_DIR / f"{material_name}_{shape}_preview.json"
    with open(preview_file, "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Preview data saved: {preview_file}")
    return str(preview_file)

def get_estimated_vertices(shape):
    """Estimate vertex count for different shapes"""
    counts = {
        "cube": 8,
        "sphere": 400,
        "cylinder": 200
    }
    return counts.get(shape, 100)

# ------------------ List Available Materials ------------------
def list_materials():
    """List all available materials with properties"""
    print("\n" + "="*60)
    print("📚 Available Materials")
    print("="*60)
    
    for name, props in MATERIAL_DATABASE.items():
        print(f"\n🔹 {name}")
        print(f"   {props['description']}")
        print(f"   Metallic: {props['metallic']:.1f} | Roughness: {props['roughness']:.1f}")
        print(f"   Color: RGB{tuple(props['color'])}")
    
    print("\n" + "="*60 + "\n")

# ------------------ Batch Rendering ------------------
def render_all_materials(shape="sphere", size=2.0):
    """Render all materials for comparison"""
    print(f"\n🎨 Rendering all materials as {shape}...\n")
    
    results = {}
    for material_name in MATERIAL_DATABASE.keys():
        result = generate_material_preview(material_name, shape, size)
        results[material_name] = result
        time.sleep(0.5)  # Small delay between renders
    
    print("\n✅ Batch rendering complete!")
    print(f"📁 All renders saved to: {RENDERS_DIR}")
    
    return results

# ------------------ Test Code ------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("JARVIS 3D Material Renderer")
    print("="*60)
    
    # Show available renderers
    print("\n📊 Renderer Status:")
    print(f"  {'✓' if PYVISTA_AVAILABLE else '✗'} PyVista (Best Quality)")
    print(f"  {'✓' if MATPLOTLIB_AVAILABLE else '✗'} Matplotlib (Good Quality)")
    
    if not PYVISTA_AVAILABLE and not MATPLOTLIB_AVAILABLE:
        print("\n⚠ No 3D renderer available!")
        print("Install at least one:")
        print("  pip install pyvista          # Recommended")
        print("  pip install matplotlib       # Fallback")
    
    print()
    
    # List materials
    list_materials()
    
    # Test renders
    print("🧪 Running test renders...\n")
    
    # Single render
    generate_material_preview("Titanium", "sphere", 1.5)
    time.sleep(1)
    generate_material_preview("Gold", "cube", 2.0)
    time.sleep(1)
    generate_material_preview("Glass", "cylinder", 1.0)
    
    # Uncomment to render all materials:
    # render_all_materials("sphere", 1.5)
    
    print("\n✅ Test complete!")