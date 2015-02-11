Plasmodium Autocount and Cell Counting Aid
===

Plasmodium Autocount is a python script for counting blood cells infected with malaria on a blood smear. With the closure of the VBC and uncertain future of the VBC website at vicbioinformatic.com, the Plasmodium Autocount code is preserved in this directory. This software was developed by Paul Harrison and Charles Ma at Monash University.

Plasmodium Autocount identifies cells using a circlular Hough transform, then looks for stained spots within cells as evidence of infection. Identified cells that are misshapen (debris on the slide) or have too much stain (white blood cells) are discarded.

**Requirements:** Python 2, Python Imaging Library, numpy, scipy

This software is described in:

  Ma, C., Harrison, P., Wang, L., & Coppel, R. L. (2010). [Automated estimation of parasitaemia of Plasmodium yoelii-infected mice by digital image analysis of Giemsa-stained thin blood smears.](http://www.malariajournal.com/content/9/1/348) Malaria Journal, 9(1), 348. doi:10.1186/1475-2875-9-348



Cell Counting Aid
---

Cell Counting Aid is software that allows users to keep records of cell counting. The information recorded includes the locations of cells and whether or not each cell is infected. Cell Counting Aid runs on the Microsoft Windows platform and was written in Visual Basic. After an image is opened with the software, the operator uses the mouse to point to each cell and clicks the left button if the cell is uninfected or the right button if it is infected. Parasitemia values (percentage of cells infected) are recalculated after each mouse click. The total number of cells and the total number of infected cells are recorded and can be exported to Excel for analysis. The file that contains the information is kept in the folder "Cell Counting" and the filename is "counting log".

To install, open the .zip file and run Setup.

**Requirements:** Microsoft Windows



Sample Images
---

sample-images.zip provides sample images, with manual annotation of infected an uninfected cells (made with Cell Counting Aid).
