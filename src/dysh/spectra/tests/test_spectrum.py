from dysh.fits.gbtfitsload import GBTFITSLoad
from dysh.util import get_project_testdata


class TestSpectrum:

    def setup_method(self):
        data_dir = get_project_testdata() / "AGBT05B_047_01"
        sdf_file = data_dir / "AGBT05B_047_01.raw.acs"
        sdf = GBTFITSLoad(sdf_file)
        getps0 = sdf.getps(51, plnum=0)
        self.ps0 = getps0.timeaverage()[0]
        getps1 = sdf.getps(51, plnum=1)
        self.ps1 = getps1.timeaverage()[0]

    def test_add(self):
        """Test that we can add two `Spectrum`."""
        addition = self.ps0 + self.ps1

        assert addition.meta["EXPOSURE"] == (self.ps0.meta["EXPOSURE"] + self.ps1.meta["EXPOSURE"])

    def test_sub(self):
        """Test that we can subtract two `Spectrum`."""
        subtraction = self.ps0 - self.ps1

        assert subtraction.meta["EXPOSURE"] == (self.ps0.meta["EXPOSURE"] + self.ps1.meta["EXPOSURE"])
