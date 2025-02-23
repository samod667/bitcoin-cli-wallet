# wallet/qrcode.py

import qrcode
from typing import Optional

def generate_ascii_qr(data: str, label: Optional[str] = "", 
                     data_type: str = "address", compact: bool = True) -> str:
    """
    Generate a compact ASCII QR code suitable for terminal display.
    
    This function creates QR codes that can be displayed directly in the terminal,
    using Unicode characters to create a more compact representation. It's
    particularly useful for displaying Bitcoin addresses and payment URIs.
    
    The function uses half-height block characters to make the QR code more
    compact while maintaining scannability. This is especially important in
    terminal displays where vertical space is often more limited than
    horizontal space.
    
    Args:
        data: The string to encode in the QR code
        label: Optional label to display above the QR code
        data_type: Type of data being encoded ('address', 'privkey', or 'pubkey')
        compact: Whether to use the compact display format
    
    Returns:
        A string containing the ASCII representation of the QR code
    """
    try:
        # Configure QR code with optimal parameters for terminal display
        qr = qrcode.QRCode(
            version=None,          # Automatically determine version
            error_correction=qrcode.constants.ERROR_CORRECT_L,  
            box_size=1,           # Minimum box size for terminal
            border=1              # Minimum border for reliable scanning
        )
        
        # For addresses, normalize the data
        if data_type == "address":
            data = data.upper().strip()
        
        # Add data and generate the QR code matrix
        qr.add_data(data)
        qr.make(fit=True)
        
        # Convert to ASCII art
        ascii_art = []
        
        # Add label if provided
        if label:
            ascii_art.append(f"- {label} -")
        
        # Generate the ASCII representation
        matrix = qr.get_matrix()
        if compact:
            # Use half-height characters for compact display
            for i in range(0, len(matrix), 2):
                line = ""
                for j in range(len(matrix[i])):
                    top = matrix[i][j]
                    # Handle the case where we're at the last row
                    bottom = matrix[i + 1][j] if i + 1 < len(matrix) else False
                    
                    # Choose the appropriate Unicode character
                    if top and bottom:
                        line += "█"  # Full block
                    elif top:
                        line += "▀"  # Upper half block
                    elif bottom:
                        line += "▄"  # Lower half block
                    else:
                        line += " "  # Empty space
                ascii_art.append(line)
        else:
            # Traditional full-height display
            for row in matrix:
                line = ""
                for cell in row:
                    line += "██" if cell else "  "
                ascii_art.append(line)
        
        return "\n".join(ascii_art)
        
    except Exception as e:
        return f"Error generating QR code: {str(e)}"