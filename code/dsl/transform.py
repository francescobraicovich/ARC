import numpy as np
from dsl.utilities.plot import plot_selection
from dsl.utilities.checks import check_axis, check_num_rotations, check_color, check_integer
from scipy.ndimage import binary_fill_holes
from dsl.utilities.transformation_utilities import create_grid3d, find_bounding_rectangle, find_bounding_square, center_of_mass
from dsl.select import Selector
from dsl.color_select import ColorSelector


# Transformer class that contains methods to transform the grid.
# The grid is a 2D numpy array, and the selection is a 3D boolean mask.
# Hence, the grid must be stacked along the third dimension to create a 3D grid, using the create_grid3d method.

# Implemented methods:
# 1 - flipv(grid, selection): Flip the grid vertically.
# 2 - fliph(grid, selection): Flip the grid horizontally.
# 3 - delete(grid, selection): Set the value of the selected cells to 0.
# 4 - rotate90(grid, selection): Rotate the selected cells 90 degrees counterclockwise.
# 5 - rotate180(grid, selection): Rotate the selected cells 180 degrees counterclockwise.
# 6 - rotate270(grid, selection): Rotate the selected cells 270 degrees counterclockwise.
# 7 - crop(grid, selection): Crop the grid to the bounding rectangle around the selection. Use -1 as the value for cells outside the selection.
# 8 - fill_with_color(grid, color, fill_color): Fills any shape of a given color with the fill_color
# 9 - mirror_main_diagonal(grid, selection): Mirror the selected region along the main diagonal (top-left to bottom-right).
# 10 - mirror_anti_diagonal(grid, selection): Mirror the selected region along the anti-diagonal (top-right to bottom-left).
# 11 - color(grid, selection, color_selected): Apply a color transformation (color_selected) to the selected cells (selection) in the grid and return a new 3D grid.   
# 12 - copy_paste(grid, selection, shift_x, shift_y): Shift the selected cells in the grid by (shift_x, shift_y).
# 13 - copy_sum(grid, selection, shift_x, shift_y): Shift the selected cells in the grid by (shift_x, shift_y) without using loops and sum the values.
# 14 - cut_paste(grid, selection, shift_x, shift_y): Shift the selected cells in the grid by (shift_x, shift_y) and set the original cells to 0.
# 15 - cut_sum(grid, selection, shift_x, shift_y): Shift the selected cells in the grid by (shift_x, shift_y) without using loops and sum the values.
# 16 - change_background_color(grid, selection, new_color): Change the background color of the grid to the specified color.
# 17 - vupscale(grid, selection, scale_factor): Upscale the selection in the grid by a specified scale factor, and cap the upscaled selection to match the original size.
# 18 - hupscale(grid, selection, scale_factor): Upscale the selection in the grid by a specified scale factor, and cap the upscaled selection to match the original size.
# 19 - fill_bounding_rectangle_with_color(grid, selection, color): Fill the bounding rectangle around the selection with the specified color.
# 20 - fill_bounding_square_with_color(grid, selection, color): Fill the bounding square around the selection with the specified color.
# 21 - mirror_horizontally(grid, selection): Mirrors the selection horizontally out of the original grid. Works only id columns < 15.
# 22 - mirror_vertically(grid, selection): Mirrors the selection vertically out of the original grid. Works only id rows < 15.
# 23 - duplicate_horizontally(grid, selection): Duplicate the selection horizontally out of the original grid. Works only if columns < 15.
# 24 - duplicate_vertically(grid, selection): Duplicate the selection vertically out of the original grid. Works only if rows < 15. 
# 25 - copy_paste_vertically(grid, selection): For each mask in the selection, copy its selected area and paste it upwards and downwards as many times as possible within the grid bounds.
# 26 - copy_paste_horizontally(grid, selection): For each mask in the selection, copy its selected area and paste it leftwards and rightwards as many times as possible within the grid bounds.


class Transformer:
    def __init__(self):
        pass

    def flipv(self, grid, selection):
        """
        Flip the grid along the specified axis.
        """
        grid_3d = create_grid3d(grid, selection) # Add an additional dimension to the grid by stacking it
        bounding_rectangle = find_bounding_rectangle(selection) # Find the bounding rectangle around the selection for each slice
        flipped_bounding_rectangle = np.flip(bounding_rectangle, axis=1) # Flip the selection along the specified axis
        grid_3d[bounding_rectangle] = np.flip(grid_3d, axis=1)[flipped_bounding_rectangle] # Flip the bounding rectangle along the specified axis
        return grid_3d
    
    def fliph(self, grid, selection):
        """
        Flip the grid along the specified axis.
        """
        grid_3d = create_grid3d(grid, selection) # Add an additional dimension to the grid by stacking it
        bounding_rectangle = find_bounding_rectangle(selection) # Find the bounding rectangle around the selection for each slice
        flipped_bounding_rectangle = np.flip(bounding_rectangle, axis=2) # Flip the selection along the specified axis
        grid_3d[bounding_rectangle] = np.flip(grid_3d, axis=2)[flipped_bounding_rectangle] # Flip the bounding rectangle along the specified axis
        return grid_3d
    
    def delete(self, grid, selection):
        """
        Set the value of the selected cells to 0.
        """
        grid_3d = create_grid3d(grid, selection)
        grid_3d[selection] = 0
        return grid_3d
    
    def rotate(self, grid, selection, num_rotations):
        """
        Rotate the selected cells 90 degrees n times counterclockwise.
        """
        grid_3d = create_grid3d(grid, selection)
        if check_num_rotations(num_rotations) == False:
            return grid_3d
        bounding_square = find_bounding_square(selection)
        rotated_bounding_square = np.rot90(bounding_square, num_rotations, axes=(1, 2))
        grid_3d[bounding_square] = np.rot90(grid_3d, num_rotations, axes=(1, 2))[rotated_bounding_square]
        return grid_3d
    
    def rotate90(self, grid, selection):
        """
        Rotate the selected cells 90 degrees counterclockwise.
        """
        return self.rotate(grid, selection, 1)

    def rotate180(self, grid, selection):
        """
        Rotate the selected cells 180 degrees counterclockwise.
        """
        return self.rotate(grid, selection, 2)
    
    def rotate270(self, grid, selection):
        """
        Rotate the selected cells 270 degrees counterclockwise.
        """
        return self.rotate(grid, selection, 3)
    
    def crop(self, grid, selection):
        """
        Crop the grid to the bounding rectangle around the selection. Use -1 as the value for cells outside the selection.
        -1 will be the same number that will be used to pad the grids in order to make them the same size.
        """
        grid_3d = create_grid3d(grid, selection)
        bounding_rectangle = find_bounding_rectangle(selection)
        grid_3d[~bounding_rectangle] = -1
        return grid_3d
    
    def color(self, grid, selection, color_selected):
        """
        Apply a color transformation (color_selected) to the selected cells (selection) in the grid and return a new 3D grid.
        """
        if check_color(color_selected) == False:
            return grid_3d
        grid_3d = create_grid3d(grid, selection)
        grid_3d[selection == 1] = color_selected
        return grid_3d

    
    def fill_with_color(self, grid, selection, fill_color): #change to take a selection and not do it alone if we want to + 3d or 2d ?
        '''
        Fill all holes inside the single connected shape of the specified color
        and return the modified 2D grid.
        '''
        grid_3d = create_grid3d(grid, selection)  

        if check_color(fill_color) == False:
            return grid_3d
        filled_masks = np.array([binary_fill_holes(i) for i in selection])
        # Fill the holes in the grids with the specified color
        new_masks = filled_masks & (~selection)
        grid_3d[new_masks] = fill_color

        return grid_3d
        
    def flip_main_diagonal(self, grid, selection):
        '''
        Mirror the selected region along the main diagonal (top-left to bottom-right).
        '''
        grid_3d = create_grid3d(grid, selection)
        bounding_square = find_bounding_square(selection)  # Find the bounding square for each selection slice

        for i in range(grid_3d.shape[0]):  # Iterate through each selection slice
            mask = bounding_square[i]  # Mask for the current bounding square
            rows, cols = np.where(mask)  # Get the indices of the selected region
            if len(rows) > 0 and len(cols) > 0:
                # Calculate the bounding square limits
                min_row, max_row = rows.min(), rows.max()
                min_col, max_col = cols.min(), cols.max()

                # Extract the square region
                square = grid_3d[i, min_row:max_row+1, min_col:max_col+1]
                # Mirror along the main diagonal
                mirrored = square.T
                # Replace the original square with the mirrored one
                grid_3d[i, min_row:max_row+1, min_col:max_col+1] = mirrored

        return grid_3d

    def flip_anti_diagonal(self, grid, selection):
        '''
        Mirror the selected region along the anti-diagonal (top-right to bottom-left).
        '''
        grid_3d = create_grid3d(grid, selection)
        bounding_square = find_bounding_square(selection)  # Find the bounding square for each selection slice

        for i in range(grid_3d.shape[0]):  # Iterate through each selection slice
            mask = bounding_square[i]  # Mask for the current bounding square
            rows, cols = np.where(mask)  # Get the indices of the selected region
            if len(rows) > 0 and len(cols) > 0:
                # Calculate the bounding square limits
                min_row, max_row = rows.min(), rows.max()
                min_col, max_col = cols.min(), cols.max()

                # Extract the square region
                square = grid_3d[i, min_row:max_row+1, min_col:max_col+1].copy()
                # Mirror along the anti-diagonal
                mirrored = np.flip((np.rot90(square)),1)
                # Replace the original square with the mirrored one
                grid_3d[i, min_row:max_row+1, min_col:max_col+1] = mirrored

        return grid_3d

    def copy_paste(self, grid, selection, shift_x, shift_y):
        """
        Shift the selected cells in the grid by (shift_x, shift_y) without using loops.
        """
        grid_3d = create_grid3d(grid, selection)

        # Get the indices where the selection is True
        layer_idxs, old_row_idxs, old_col_idxs = np.where(selection)

        # Compute the new coordinates after shifting
        new_row_idxs = old_row_idxs + shift_y  # Shift rows (vertical)
        new_col_idxs = old_col_idxs + shift_x  # Shift columns (horizontal)

        # Filter out coordinates that are out of bounds
        valid_mask = (
            (new_row_idxs >= 0) & (new_row_idxs < grid_3d.shape[1]) &
            (new_col_idxs >= 0) & (new_col_idxs < grid_3d.shape[2])
        )

        # Apply the valid mask to indices and coordinates
        layer_idxs = layer_idxs[valid_mask]
        old_row_idxs = old_row_idxs[valid_mask]
        old_col_idxs = old_col_idxs[valid_mask]
        new_row_idxs = new_row_idxs[valid_mask]
        new_col_idxs = new_col_idxs[valid_mask]

        # Get the values to copy
        values = grid_3d[layer_idxs, old_row_idxs, old_col_idxs]

        # Copy the values to the new positions
        grid_3d[layer_idxs, new_row_idxs, new_col_idxs] = values

        return grid_3d
    

    def copy_sum(self, grid, selection, shift_x, shift_y):
        """
        Shift the selected cells in the grid by (shift_x, shift_y) without using loops.
        """
        grid_3d = create_grid3d(grid, selection)

        # Get the indices where the selection is True
        layer_idxs, old_row_idxs, old_col_idxs = np.where(selection)

        # Compute the new coordinates after shifting
        new_row_idxs = old_row_idxs + shift_y  # Shift rows (vertical)
        new_col_idxs = old_col_idxs + shift_x  # Shift columns (horizontal)

        # Filter out coordinates that are out of bounds
        valid_mask = (
            (new_row_idxs >= 0) & (new_row_idxs < grid_3d.shape[1]) &
            (new_col_idxs >= 0) & (new_col_idxs < grid_3d.shape[2])
        )

        # Apply the valid mask to indices and coordinates
        layer_idxs = layer_idxs[valid_mask]
        old_row_idxs = old_row_idxs[valid_mask]
        old_col_idxs = old_col_idxs[valid_mask]
        new_row_idxs = new_row_idxs[valid_mask]
        new_col_idxs = new_col_idxs[valid_mask]

        # Get the values to copy
        values = grid_3d[layer_idxs, old_row_idxs, old_col_idxs]

        # Copy the values to the new positions
        np.add.at(grid_3d, (layer_idxs, new_row_idxs, new_col_idxs), values)

        return grid_3d
    
    def cut_paste(self, grid, selection, shift_x, shift_y):
        """
        Shift the selected cells in the grid by (shift_x, shift_y) without using loops.
        """
        grid_3d = create_grid3d(grid, selection)

        # Get the indices where the selection is True
        layer_idxs, old_row_idxs, old_col_idxs = np.where(selection)

        # Compute the new coordinates after shifting
        new_row_idxs = old_row_idxs + shift_y  # Shift rows (vertical)
        new_col_idxs = old_col_idxs + shift_x  # Shift columns (horizontal)

        # Filter out coordinates that are out of bounds
        valid_mask = (
            (new_row_idxs >= 0) & (new_row_idxs < grid_3d.shape[1]) &
            (new_col_idxs >= 0) & (new_col_idxs < grid_3d.shape[2])
        )

        # Get the values to move
        values = grid_3d[layer_idxs[valid_mask], old_row_idxs[valid_mask], old_col_idxs[valid_mask]]

        # Clear the original positions
        grid_3d[layer_idxs, old_row_idxs, old_col_idxs] = 0

        # Assign the values to the new positions
        grid_3d[layer_idxs[valid_mask], new_row_idxs[valid_mask], new_col_idxs[valid_mask]] = values

        return grid_3d


    def cut_sum(self, grid, selection, shift_x, shift_y):
        """
        Shift the selected cells in the grid by (shift_x, shift_y) without using loops.
        """
        grid_3d = create_grid3d(grid, selection)

        # Get the indices where the selection is True
        layer_idxs, old_row_idxs, old_col_idxs = np.where(selection)

        # Compute the new coordinates after shifting
        new_row_idxs = old_row_idxs + shift_y  # Shift rows (vertical)
        new_col_idxs = old_col_idxs + shift_x  # Shift columns (horizontal)

        # Filter out coordinates that are out of bounds
        valid_mask = (
            (new_row_idxs >= 0) & (new_row_idxs < grid_3d.shape[1]) &
            (new_col_idxs >= 0) & (new_col_idxs < grid_3d.shape[2])
        )

        # Get the values to move
        values = grid_3d[layer_idxs[valid_mask], old_row_idxs[valid_mask], old_col_idxs[valid_mask]]

        # Clear the original positions
        grid_3d[layer_idxs, old_row_idxs, old_col_idxs] = 0

        # Paste the values to the new positions adding them to the existing values
        np.add.at(grid_3d, (layer_idxs[valid_mask], new_row_idxs[valid_mask], new_col_idxs[valid_mask]), values)

        return grid_3d
    

    def change_background_color(self, grid, selection, new_color):
        '''
        Change the background color of the grid to the specified color.
        '''
    
        grid3d = create_grid3d(grid, selection)
        color_selector = ColorSelector()
        background_color = color_selector.mostcolor(grid) # Get the most common color in the grid
        grid3d[grid3d == background_color] = new_color # Change the background color to the specified color

        if check_color(new_color) == False: # Check if the color is valid
            return grid3d
        
        return grid3d
    
    def change_selection_to_background_color(self, grid, selection):
        '''
        Change the selected cells in the grid to the background color.
        ''' 
        color_selector = ColorSelector()
        background_color = color_selector.mostcolor(grid)
        grid_3d = create_grid3d(grid, selection)
        grid_3d[selection == 1] = background_color

        return grid_3d

    def vupscale(self, grid, selection, scale_factor):
        """
        Upscale the selection in the grid by a specified scale factor, 
        and cap the upscaled selection to match the original size.
        """
        # Create a 3D grid representation
        selection_3d_grid = create_grid3d(grid, selection)
        depth, original_rows, original_cols = np.shape(selection)

        # Perform upscaling by repeating elements along rows
        upscaled_selection = np.repeat(selection, scale_factor, axis=1)
        upscaled_selection_3d_grid = np.repeat(selection_3d_grid, scale_factor, axis=1)

        # Calculate row boundaries for capping
        if original_rows % 2 == 0:
            half_rows_top, half_rows_bottom = original_rows // 2, original_rows // 2
        else:
            half_rows_top, half_rows_bottom = original_rows // 2 + 1, original_rows // 2

        # Initialize arrays for capped selection and grid
        capped_selection = np.zeros((depth, original_rows, original_cols), dtype=bool)
        capped_upscaled_grid = np.zeros((depth, original_rows, original_cols))

        for layer_idx in range(depth):
            # Compute center of mass for the original and upscaled selection
            original_com = center_of_mass(selection[layer_idx])[0]
            upscaled_com = center_of_mass(upscaled_selection[layer_idx])[0]

            # Determine bounds for capping
            lower_bound = min(int(upscaled_com + half_rows_bottom), original_rows * scale_factor)
            upper_bound = max(int(upscaled_com - half_rows_top), 0)

            # Adjust bounds if out of range
            if lower_bound >= original_rows * scale_factor:
                lower_bound = original_rows * scale_factor
                upper_bound = lower_bound - original_rows
            elif upper_bound <= 0:
                upper_bound = 0
                lower_bound = upper_bound + original_rows

            # Apply capping and recalculate center of mass
            capped_selection[layer_idx] = upscaled_selection[layer_idx, upper_bound:lower_bound, :]
            capped_com = center_of_mass(capped_selection[layer_idx])[0]

            # Adjust bounds based on center of mass difference
            offset = capped_com - original_com
            lower_bound += offset
            upper_bound += offset

            # Reapply bounds check
            if lower_bound >= original_rows * scale_factor:
                lower_bound = original_rows * scale_factor
                upper_bound = lower_bound - original_rows
            elif upper_bound <= 0:
                upper_bound = 0
                lower_bound = upper_bound + original_rows

            # Final capping
            capped_selection[layer_idx] = upscaled_selection[layer_idx, upper_bound:lower_bound, :]
            capped_upscaled_grid[layer_idx] = upscaled_selection_3d_grid[layer_idx, upper_bound:lower_bound, :]

        # Update the original grid with the capped selection
        selection_3d_grid[selection == 1] = 0
        selection_3d_grid[capped_selection] = capped_upscaled_grid[capped_selection].ravel()

        return selection_3d_grid

  
    def hupscale(self, grid, selection, scale_factor):
        """
        Upscale the selection in the grid horizontally by a specified scale factor,
        and cap the upscaled selection to match the original size.
        """
        # Create a 3D grid representation
        selection_3d_grid = create_grid3d(grid, selection)
        depth, original_rows, original_cols = selection.shape

        # Perform upscaling by repeating elements along columns
        upscaled_selection = np.repeat(selection, scale_factor, axis=2)
        upscaled_selection_3d_grid = np.repeat(selection_3d_grid, scale_factor, axis=2)
        upscaled_cols = upscaled_selection.shape[2]

        # Calculate column boundaries for capping
        if original_cols % 2 == 0:
            half_cols_left, half_cols_right = original_cols // 2, original_cols // 2
        else:
            half_cols_left, half_cols_right = original_cols // 2 + 1, original_cols // 2

        # Initialize arrays for capped selection and grid
        capped_selection = np.zeros((depth, original_rows, original_cols), dtype=bool)
        capped_upscaled_grid = np.zeros((depth, original_rows, original_cols))

        for layer_idx in range(depth):
            # Compute center of mass for the original and upscaled selection
            original_com = center_of_mass(selection[layer_idx])[1]
            upscaled_com = center_of_mass(upscaled_selection[layer_idx])[1]

            # Determine bounds for capping
            lower_bound = min(int(upscaled_com + half_cols_right), upscaled_cols)
            upper_bound = max(int(upscaled_com - half_cols_left), 0)

            # Adjust bounds if out of range
            if lower_bound >= upscaled_cols:
                lower_bound = upscaled_cols
                upper_bound = lower_bound - original_cols
            elif upper_bound <= 0:
                upper_bound = 0
                lower_bound = upper_bound + original_cols

            # Apply capping and recalculate center of mass
            capped_selection[layer_idx] = upscaled_selection[layer_idx, :, upper_bound:lower_bound]
            capped_com = center_of_mass(capped_selection[layer_idx])[1]

            # Adjust bounds based on center of mass difference
            offset = int(capped_com - original_com)
            lower_bound += offset
            upper_bound += offset

            # Reapply bounds check
            if lower_bound >= upscaled_cols:
                lower_bound = upscaled_cols
                upper_bound = lower_bound - original_cols
            elif upper_bound <= 0:
                upper_bound = 0
                lower_bound = upper_bound + original_cols

            # Final capping
            capped_selection[layer_idx] = upscaled_selection[layer_idx, :, upper_bound:lower_bound]
            capped_upscaled_grid[layer_idx] = upscaled_selection_3d_grid[layer_idx, :, upper_bound:lower_bound]

        # Update the original grid with the capped selection
        selection_3d_grid[selection == 1] = 0
        capped_mask = capped_selection.astype(bool)
        selection_3d_grid[capped_mask] = capped_upscaled_grid[capped_mask].ravel()

        return selection_3d_grid


    def fill_bounding_rectangle_with_color(self, grid, selection, color):
        '''
        Fill the bounding rectangle around the selection with the specified color.
        '''
        if check_color(color) == False:
            return grid
        grid_3d = create_grid3d(grid, selection)
        bounding_rectangle = find_bounding_rectangle(selection)
        grid_3d[bounding_rectangle & (~selection)] = color
        return grid_3d
    
    def fill_bounding_square_with_color(self, grid, selection, color):
        '''
        Fill the bounding square around the selection with the specified color.
        '''
        if check_color(color) == False:
            return grid
        grid_3d = create_grid3d(grid, selection)
        bounding_square = find_bounding_square(selection)
        grid_3d[bounding_square & (~selection)] = color
        return grid_3d
    
    def mirror_horizontally(self, grid, selection):
        '''
        Mirrors the selection horizontally out of the original grid. Works only id columns < 15.
        '''
        d, rows, cols = np.shape(selection)
        if cols > 15:
            return grid
        grid_3d = create_grid3d(grid, selection)
        new_grid_3d = np.zeros((d, rows, cols * 2))
        new_grid_3d[:, :, :cols] = grid_3d
        new_grid_3d[:, :, cols:] = np.flip(grid_3d, axis=2)
        flipped_selection = np.flip(selection, axis=2)
        new_grid_3d[:, :, cols:][~flipped_selection] = 0
        return new_grid_3d
    
    def mirror_vertically(self, grid, selection):
        '''
        Mirrors the selection vertically out of the original grid. Works only id rows < 15.
        '''
        d, rows, cols = np.shape(selection)
        if rows > 15:
            return grid
        grid_3d = create_grid3d(grid, selection)
        new_grid_3d = np.zeros((d, rows * 2, cols))
        new_grid_3d[:, :rows, :] = grid_3d
        new_grid_3d[:, rows:, :] = np.flip(grid_3d, axis=1)
        flipped_selection = np.flip(selection, axis=1)
        new_grid_3d[:, rows:, :][~flipped_selection] = 0
        return new_grid_3d
    
    def duplicate_horizontally(self, grid, selection):
        """
        Duplicate the selection horizontally out of the original grid. Works only if columns < 15.
        """
        d, rows, cols = np.shape(selection)
        if cols > 15:
            return grid
        grid_3d = create_grid3d(grid, selection)
        new_grid_3d = np.zeros((d, rows, cols * 2))
        new_grid_3d[:, :, :cols] = grid_3d
        new_grid_3d[:, :, cols:][selection] = grid_3d[selection]
        return new_grid_3d
    
    def duplicate_vertically(self, grid, selection):
        """
        Duplicate the selection vertically out of the original grid. Works only if rows < 15.
        """
        d, rows, cols = np.shape(selection)
        if rows > 15:
            return grid
        grid_3d = create_grid3d(grid, selection)
        new_grid_3d = np.zeros((d, rows * 2, cols))
        new_grid_3d[:, :rows, :] = grid_3d
        new_grid_3d[:, rows:, :][selection] = grid_3d[selection]
        return new_grid_3d
    
    def copy_paste_vertically(self, grid, selection):
        """
        For each mask in the selection, copy its selected area and paste it upwards and downwards
        as many times as possible within the grid bounds.
        """
        grid_3d = create_grid3d(grid, selection)
        n_masks, height_of_grid, width_of_grid = grid_3d.shape

        # Identify rows with at least one '1' in each mask
        rows_with_one = np.any(selection == 1, axis=2)  # Shape: (n_masks, rows)

        # Initialize arrays for first and last rows containing '1's
        first_rows = np.full(n_masks, -1)
        last_rows = np.full(n_masks, -1)

        # Find first and last rows with '1's in each mask
        for idx in range(n_masks):
            row_indices = np.where(rows_with_one[idx])[0]
            if row_indices.size > 0:
                first_rows[idx] = row_indices[0]
                last_rows[idx] = row_indices[-1]

        # Calculate the height of the selection per mask
        selection_height = last_rows - first_rows + 1  # Shape: (n_masks,)
        # Calculate factors per mask
        factor_up = np.ceil(first_rows / selection_height).astype(int)
        factor_down = np.ceil((height_of_grid - last_rows - 1) / selection_height).astype(int)
        # Initialize the final transformation
        final_transformation = grid_3d.copy()

        # Loop over each mask
        for idx in range(n_masks):
            if selection_height[idx] <= 0:
                # Skip masks with no selection
                continue

            # Get the grid and selection for the current mask
            grid_layer = final_transformation[idx]
            selection_layer = selection[idx]
            # Reshape to 3D arrays to match the input of copy_paste
            grid_layer_3d = np.expand_dims(grid_layer, axis=0)
            selection_layer_3d = np.expand_dims(selection_layer, axis=0)

            # Copy-paste upwards
            for i in range(factor_up[idx]):
                shift = -(i+1) * selection_height[idx]
                # Perform the copy-paste
                grid_layer_3d = self.copy_paste(grid_layer_3d, selection_layer_3d, 0, shift) #todo verify this part
            # Copy-paste downwards
            for i in range(factor_down[idx]):
                shift = (i+1) * selection_height[idx]
                # Perform the copy-paste
                grid_layer_3d = self.copy_paste(grid_layer_3d, selection_layer_3d, 0, shift)

            # Remove the extra dimension and update the final transformation
            final_transformation[idx] = grid_layer_3d[0]

        return final_transformation

    def copy_paste_horizontally(self, grid, selection):
        """
        For each mask in the selection, copy its selected area and paste it leftwards and rightwards
        as many times as possible within the grid bounds.
        """
        grid_3d = create_grid3d(grid, selection)
        n_masks, height_of_grid, width_of_grid = grid_3d.shape
    
        # Identify columns with at least one '1' in each mask
        columns_with_one = np.any(selection == 1, axis=1)  # Shape: (n_masks, columns)
    
        # Initialize arrays for first and last columns containing '1's
        first_cols = np.full(n_masks, -1)
        last_cols = np.full(n_masks, -1)
    
        # Find first and last columns with '1's in each mask
        for idx in range(n_masks):
            col_indices = np.where(columns_with_one[idx])[0]
            if col_indices.size > 0:
                first_cols[idx] = col_indices[0]
                last_cols[idx] = col_indices[-1]
    
        # Calculate the width of the selection per mask
        selection_width = last_cols - first_cols + 1  # Shape: (n_masks,)
        # Calculate factors per mask
        factor_left = np.ceil(first_cols / selection_width).astype(int)
        factor_right = np.ceil((width_of_grid - last_cols - 1) / selection_width).astype(int)
        # Initialize the final transformation
        final_transformation = grid_3d.copy()
    
        # Loop over each mask
        for idx in range(n_masks):
            if selection_width[idx] <= 0:
                # Skip masks with no selection
                continue
    
            # Get the grid and selection for the current mask
            grid_layer = final_transformation[idx]
            selection_layer = selection[idx]
            # Reshape to 3D arrays to match the input of copy_paste
            grid_layer_3d = np.expand_dims(grid_layer, axis=0)
            selection_layer_3d = np.expand_dims(selection_layer, axis=0)
    
            # Copy-paste leftwards
            for i in range(factor_left[idx]):
                shift = -(i + 1) * selection_width[idx]
                # Perform the copy-paste
                grid_layer_3d = self.copy_paste(grid_layer_3d, selection_layer_3d, shift, 0)
            # Copy-paste rightwards
            for i in range(factor_right[idx]):
                shift = (i + 1) * selection_width[idx]
                # Perform the copy-paste
                grid_layer_3d = self.copy_paste(grid_layer_3d, selection_layer_3d, shift, 0)
    
            # Remove the extra dimension and update the final transformation
            final_transformation[idx] = grid_layer_3d[0]
    
        return final_transformation
