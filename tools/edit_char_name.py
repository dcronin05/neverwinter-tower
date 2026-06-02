# ==============================================================================
# AI DISCLAIMER
# This file was programmatically generated and edited by Antigravity, an AI assistant.
# Please review the code for security and compatibility before production use.
# ==============================================================================

import struct
import sys
import os

def edit_gff_name(input_path, output_path, new_first_name, new_last_name):
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Read Header
    sig = data[0:4]
    ver = data[4:8]
    struct_offset, struct_count = struct.unpack('<II', data[8:16])
    field_offset, field_count = struct.unpack('<II', data[16:24])
    label_offset, label_count = struct.unpack('<II', data[24:32])
    data_offset, data_count = struct.unpack('<II', data[32:40])
    field_indices_offset, field_indices_count = struct.unpack('<II', data[40:48])
    list_indices_offset, list_indices_count = struct.unpack('<II', data[48:56])
    
    # Read Label Table
    labels = []
    for i in range(label_count):
        start = label_offset + i * 16
        label_bytes = data[start:start+16]
        # Label is null-padded up to 16 bytes
        label_str = label_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
        labels.append(label_str)
        
    first_name_label_idx = None
    last_name_label_idx = None
    for idx, label in enumerate(labels):
        if label == "FirstName":
            first_name_label_idx = idx
        elif label == "LastName":
            last_name_label_idx = idx
            
    if first_name_label_idx is None or last_name_label_idx is None:
        print("Could not find FirstName or LastName labels in GFF.")
        return False
        
    # Helper to construct a CEXOLOCSTRING block
    def make_loc_string(text):
        encoded = text.encode('utf-8')
        # Structure:
        # StringRef (int32): -1 (0xFFFFFFFF)
        # StringCount (uint32): 1
        # LanguageID (int32): 0
        # StringLength (uint32): len(encoded)
        # StringData: encoded bytes
        loc_data = struct.pack('<iIiiI', -1, 1, 0, 0, len(encoded)) + encoded
        # Prepend Size (uint32) of the loc_data block
        size = len(loc_data)
        return struct.pack('<I', size) + loc_data

    new_first_loc = make_loc_string(new_first_name)
    new_last_loc = make_loc_string(new_last_name)
    
    # We will locate the fields for FirstName and LastName
    first_name_field_idx = None
    last_name_field_idx = None
    
    for i in range(field_count):
        f_start = field_offset + i * 12
        f_type, f_label_idx, f_val_or_offset = struct.unpack('<III', data[f_start:f_start+12])
        if f_type == 12: # CEXOLOCSTRING
            if f_label_idx == first_name_label_idx:
                first_name_field_idx = i
            elif f_label_idx == last_name_label_idx:
                last_name_field_idx = i

    if first_name_field_idx is None or last_name_field_idx is None:
        print("Could not find FirstName or LastName fields of type CEXOLOCSTRING.")
        return False
        
    # We will perform the updates one by one.
    # To keep offset adjustments simple, we process from the largest file offset to the smallest.
    fields_to_mod = []
    for f_idx in (first_name_field_idx, last_name_field_idx):
        f_start = field_offset + f_idx * 12
        f_type, f_label_idx, f_val_or_offset = struct.unpack('<III', data[f_start:f_start+12])
        new_loc = new_first_loc if f_idx == first_name_field_idx else new_last_loc
        fields_to_mod.append({
            'field_idx': f_idx,
            'offset_in_data': f_val_or_offset,
            'new_data': new_loc
        })
        
    # Sort fields by their data offset in descending order
    fields_to_mod.sort(key=lambda x: x['offset_in_data'], reverse=True)
    
    current_data_block = data[data_offset : data_offset + data_count]
    
    # We need to trace all fields in the GFF and adjust their offsets if they point
    # after our modification point.
    # A GFF file has Fields that point to data_offset if type > 5 and type != 8.
    # Let's write a helper to modify the data block and shift offsets
    for mod in fields_to_mod:
        offset = mod['offset_in_data']
        new_bytes = mod['new_data']
        
        # Read old size
        old_size_bytes = current_data_block[offset : offset + 4]
        old_size = struct.unpack('<I', old_size_bytes)[0]
        old_total_len = 4 + old_size
        
        # Replace in current_data_block
        prefix = current_data_block[:offset]
        suffix = current_data_block[offset + old_total_len:]
        current_data_block = prefix + new_bytes + suffix
        
        # Shift size difference
        diff = len(new_bytes) - old_total_len
        
        # Adjust all field offsets pointing after this offset
        for i in range(field_count):
            f_start = field_offset + i * 12
            f_type, f_label_idx, f_val_or_offset = struct.unpack('<III', data[f_start:f_start+12])
            if f_type > 5 and f_type != 8:
                if f_val_or_offset > offset:
                    new_val_or_offset = f_val_or_offset + diff
                    data[f_start+8 : f_start+12] = struct.pack('<I', new_val_or_offset)

    # Reconstruct the file:
    # 1. Update GFF data block and its size in the header
    new_data_count = len(current_data_block)
    data[36:40] = struct.pack('<I', new_data_count)
    
    # 2. Update subsequent offsets in the header if they sit after data_offset
    header_diff = new_data_count - data_count
    
    header_offsets = [
        (40, field_indices_offset),
        (48, list_indices_offset)
    ]
    for h_pos, h_val in header_offsets:
        if h_val > data_offset:
            data[h_pos : h_pos+4] = struct.pack('<I', h_val + header_diff)
            
    # 3. Assemble the file segments:
    # Segment 1: Header to Data Block
    segment_before_data = data[:data_offset]
    # Segment 2: Updated Data Block
    # Segment 3: Rest of the GFF content (which we must shift in position)
    segment_after_data = data[data_offset + data_count:]
    
    final_data = segment_before_data + current_data_block + segment_after_data
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f_out:
        f_out.write(final_data)
        
    print(f"Successfully created character sheet {output_path} with name {new_first_name} {new_last_name}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python edit_char_name.py <input_path> <output_path> <first_name> [last_name]")
        sys.exit(1)
    first_name = sys.argv[3]
    last_name = sys.argv[4] if len(sys.argv) > 4 else ""
    edit_gff_name(sys.argv[1], sys.argv[2], first_name, last_name)
