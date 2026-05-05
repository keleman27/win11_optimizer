import sys
sys.path.insert(0, r"c:\Users\kiril\Music\win11_optimizer")

import customtkinter as ctk

def test():
    root = ctk.CTk()
    root.geometry("400x300")
    
    # Simulate DashboardFrame structure: CTkScrollableFrame containing progress bars
    scroll = ctk.CTkScrollableFrame(root, fg_color="#111114")
    scroll.pack(fill="both", expand=True)
    
    for i in range(3):
        frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)
        
        pb = ctk.CTkProgressBar(frame, height=6, corner_radius=3, fg_color="#28282D", progress_color="#4F8EF7")
        pb.pack(fill="x", pady=(4, 0))
        pb.set(0.5)
    
    root.after(2000, root.destroy)
    root.mainloop()
    print("OK")

test()
