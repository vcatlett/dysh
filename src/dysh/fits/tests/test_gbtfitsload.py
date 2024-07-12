import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from astropy.io import fits
from pandas.testing import assert_frame_equal, assert_series_equal

import dysh
from dysh import util
from dysh.fits import gbtfitsload


class TestGBTFITSLoad:
    """ """

    def setup_method(self):
        self.root_dir = util.get_project_root()
        self.data_dir = f"{self.root_dir}/testdata"
        self._file_list = glob.glob(f"{self.data_dir}/TGBT21A_501_11/*.fits")

    def test_load(self):
        """
        Test loading 8 different sdfits files.
        Check: number of pandas rows loaded is equal to the expected number.
        """
        expected = {
            "TGBT21A_501_11.raw.vegas.fits": 4,
            "TGBT21A_501_11_getps_scan_152_intnum_0_ifnum_0_plnum_0.fits": 1,
            "TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_cal_state_0.fits": 1,
            "TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_cal_state_1.fits": 1,
            "TGBT21A_501_11_ifnum_0_int_0-2.fits": 24,
            "TGBT21A_501_11_ifnum_0_int_0-2_getps_152_plnum_0.fits": 1,
            "TGBT21A_501_11_ifnum_0_int_0-2_getps_152_plnum_1.fits": 1,
            "TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0.fits": 1,
            "TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_eqweight.fits": 1,
            "TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_keepints.fits": 152,
            "TGBT21A_501_11_scan_152_ifnum_0_plnum_0.fits": 302,
            "getps_154_ifnum_0_plnum_0_intnum_0.fits": 1,
            "TGBT21A_501_11.raw.156.fits": 7,
            "testselection.fits": 50,
            "TGBT21A_501_11_getps_scan_152_ifnum_0_plnum_0_smthoff_15.fits": 1,
            "TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_state_1.fits": 1,
            "TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_state_0.fits": 1,
            "TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_all.fits": 1,
        }

        for fnm in self._file_list:
            print(fnm)

            filename = os.path.basename(fnm)
            sdf = gbtfitsload.GBTFITSLoad(fnm)
            assert len(sdf.index(bintable=0)) == expected[filename]

    def test_getspec(self):
        """
        Test that a GBTFITSLoad object can use the `getspec` function.
        """

        sdf_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11.raw.vegas.fits"
        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        spec = sdf.getspec(0)

    def test_getps_single_int(self):
        """
        Compare gbtidl result to dysh for a getps spectrum from a single integration/pol/feed.
        For the differenced spectrum (gbtidl - dysh) we check:
         - median is 0.0
         - all non-nan values are less than 5e-7
         - index 3072 is nan (why?)
        """
        gbtidl_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11_getps_scan_152_intnum_0_ifnum_0_plnum_0.fits"
        # We should probably use dysh to open the file...
        hdu = fits.open(gbtidl_file)
        gbtidl_getps = hdu[1].data["DATA"][0]

        sdf_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11.raw.vegas.fits"
        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        # psscan is a ScanList
        psscan = sdf.getps(152)
        assert len(psscan) == 1
        psscan.calibrate()
        dysh_getps = psscan[0].calibrated(0).flux.to("K").value

        diff = gbtidl_getps - dysh_getps
        hdu.close()
        assert np.nanmedian(diff) == 0.0
        assert np.all(abs(diff[~np.isnan(diff)]) < 5e-7)
        assert np.isnan(diff[3072])

    def test_getps_acs(self):
        """
        Compare `GBTIDL` result to `dysh` with ACS data.
        """

        data_dir = util.get_project_testdata() / "AGBT05B_047_01"
        sdf_file = data_dir / "AGBT05B_047_01.raw.acs"
        idl_file = data_dir / "gbtidl" / "AGBT05B_047_01.getps.acs.fits"

        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        getps = sdf.getps(scan=51, ifnum=0, plnum=0)
        ps = getps.timeaverage()
        ps_vals = ps.flux.value

        hdu = fits.open(idl_file)
        table = hdu[1].data
        gbtidl_spec = table["DATA"][0]
        hdu.close()

        # Do not compare NaN values.
        mask = np.isnan(ps_vals) | np.isnan(gbtidl_spec)

        # Compare data.
        diff = ps_vals[~mask] - gbtidl_spec[~mask]
        # try:
        assert np.all(diff < 1e-3)
        # except AssertionError:
        #    print(f"Comparison with GBTIDL ACS Spectrum failed, mean difference is {np.nanmean(diff)}")

        for col in table.names:
            if col not in ["DATA"]:
                try:
                    ps.meta[col]
                except KeyError:
                    continue
                try:
                    assert ps.meta[col] == pytest.approx(table[col][0], 1e-3)
                except AssertionError:
                    print(f"{col} fails: {ps.meta[col]}, {table[col][0]}")

    def test_gettp(self):
        """
        Compare gbtidl result to dysh for a gettp spectrum from a single polarization and feed and
        different cal states.
        For the differenced spectrum (gbtidl - dysh) we check:
        For the noise calibration diode on, off, and both:
         - mean value is 0.0
        """
        # Get the answer from GBTIDL.
        gbtidl_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_cal_state_1.fits"
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        hdu.close()

        # Get the answer from dysh.
        sdf_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11.raw.vegas.fits"
        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        tps_on = sdf.gettp(scan=152, sig=True, cal=True, calibrate=True, ifnum=0, plnum=0)
        assert len(tps_on) == 1

        # Compare.
        tp0 = tps_on[0].total_power(0)
        diff = tp0.flux.value - gbtidl_gettp
        assert np.nanmean(diff) == 0.0
        assert abs(tp0.meta["EXPOSURE"] - 0.97587454) < 1e-8
        assert abs(tp0.meta["TSYS"] - 17.458052) < 1e-6

        # Now with the noise diode Off.
        tps_off = sdf.gettp(scan=152, sig=True, cal=False, calibrate=True, ifnum=0, plnum=0)
        assert len(tps_off) == 1
        gbtidl_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0_cal_state_0.fits"
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        tp0 = tps_off[0].total_power(0)
        diff = tp0.flux.value - gbtidl_gettp
        hdu.close()
        assert np.nanmean(diff) == 0.0
        assert abs(tp0.meta["EXPOSURE"] - 0.97587454) < 1e-8
        assert abs(tp0.meta["TSYS"] - 17.458052) < 1e-6

        # Now, both on and off.
        tps = sdf.gettp(scan=152, sig=None, cal=None, calibrate=True, ifnum=0, plnum=0)
        assert len(tps) == 1
        gbtidl_file = f"{self.data_dir}/TGBT21A_501_11/TGBT21A_501_11_gettp_scan_152_ifnum_0_plnum_0.fits"
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        tp0 = tps[0].total_power(0)
        diff = tp0.flux.value - gbtidl_gettp
        hdu.close()
        assert np.nanmean(diff) == 0.0
        assert abs(tp0.meta["EXPOSURE"] - 1.9517491) < 1.5e-8
        assert abs(tp0.meta["TSYS"] - 17.458052) < 1e-6
        # now do some sig=F data

        sdf_file = f"{self.data_dir}/TGBT21A_504_01/TGBT21A_504_01.raw.vegas/TGBT21A_504_01.raw.vegas.A.fits"
        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        tps = sdf.gettp(scan=20, ifnum=0, plnum=1, sig=False, cal=True)
        gbtidl_file = (
            f"{self.data_dir}/TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_state_1.fits"
        )
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        tp0 = tps[0].timeaverage()
        diff = tp0.flux.value - gbtidl_gettp
        hdu.close()
        # assert np.nanmean(diff) == 0.0

        tps = sdf.gettp(scan=20, ifnum=0, plnum=1, sig=False, cal=False)
        gbtidl_file = (
            f"{self.data_dir}/TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_state_0.fits"
        )
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        tp0 = tps[0].timeaverage()
        diff = tp0.flux.value - gbtidl_gettp
        hdu.close()
        # assert np.nanmean(diff) == 0.0

        tps = sdf.gettp(scan=20, ifnum=0, plnum=1, sig=False, cal=None)
        gbtidl_file = (
            f"{self.data_dir}/TGBT21A_504_01/TGBT21A_504_01_gettp_scan_20_ifnum_0_plnum_1_sig_state_0_cal_all.fits"
        )
        hdu = fits.open(gbtidl_file)
        gbtidl_gettp = hdu[1].data["DATA"][0]
        tp0 = tps[0].timeaverage()
        diff = tp0.flux.value - gbtidl_gettp
        hdu.close()
        # assert np.nanmean(diff) == 0.0

    def test_load_multifits(self):
        """
        Loading multiple SDFITS files under a directory.
        It checks that

        * the GBTFITSLoad object has the correct number of IFs
        * the GBTFITSLoad object has the correct number of polarizations
        * the GBTFITSLoad object has the correct number of beams
        """

        fits_path = f"{self.data_dir}/AGBT18B_354_03/AGBT18B_354_03.raw.vegas"

        sdf = gbtfitsload.GBTFITSLoad(fits_path)

        # Check IFNUMs.
        ifnums = np.sort(sdf.udata("IFNUM"))
        assert np.sum(np.subtract(ifnums, [0, 1, 2, 3])) == 0

        # Check PLNUMs.
        plnums = np.sort(sdf.udata("PLNUM"))
        assert np.sum(np.subtract(plnums, [0, 1])) == 0

        # Check FDNUMs.
        fdnums = np.sort(sdf.udata("FDNUM"))
        assert len(fdnums) == 1
        assert np.sum(np.subtract(fdnums, [0])) == 0

    # @pytest.mark.skip(reason="We need to update this to work with multifits and ScanBlocks")
    def test_multifits_getps_offon(self):
        """
        Loading multiple SDFITS files under a directory.
        It checks that

        * getps works on all IFs
        *
        """
        proj_dir = f"{self.data_dir}/AGBT18B_354_03"
        # Load the data.
        fits_dir = f"{proj_dir}/AGBT18B_354_03.raw.vegas"
        sdf = gbtfitsload.GBTFITSLoad(fits_dir)

        # Check one IF.
        ps_scans = sdf.getps(6, ifnum=2)
        ps_spec = ps_scans[0].calibrated(0).flux.to("K").value

        gbtidl_dir = f"{proj_dir}/gbtidl_outputs"
        hdu = fits.open(f"{gbtidl_dir}/getps_scan_6_ifnum_2_plnum_0_intnum_0.fits")
        table = hdu[1].data
        gbtidl_spec = table["DATA"]

        diff = ps_spec.astype(np.float32) - gbtidl_spec[0]
        hdu.close()
        # assert np.all((ps_spec.astype(np.float32) - gbtidl_spec) == 0)
        assert np.all(abs(diff[~np.isnan(diff)]) < 7e-5)
        assert table["EXPOSURE"] == ps_scans[0].calibrated(0).meta["EXPOSURE"]
        assert np.all(abs(diff[~np.isnan(diff)]) < 7e-5)

    def test_summary(self):
        """Test that some of the columns in the summary
        match the ones produced by `GBTIDL`."""

        def read_gbtidl_summary(filename, idx=1):
            """ """
            with open(filename, "r") as log:
                lines = log.readlines()
            lines.pop(idx)
            tmp = Path(f"{filename}.tmp")
            with open(tmp, "w") as f:
                for line in lines:
                    f.write(line)

            df = pd.read_fwf(f"{filename}.tmp")
            # Clean up.
            tmp.unlink()

            return df

        cols = {
            "SCAN": "Scan",
            "OBJECT": "Source",
            "VELOCITY": "Vel",
            # "PROC": "Proc", # GBTIDL trims the names.
            "PROCSEQN": "Seq",
            "# IF": "nIF",
            "# INT": "nInt",
            "# FEED": "nFd",
        }

        path = util.get_project_testdata() / "AGBT05B_047_01"
        sdf_file = path / "AGBT05B_047_01.raw.acs"
        sdf = gbtfitsload.GBTFITSLoad(sdf_file)
        dysh_df = sdf.summary()

        gbtidl_summary = read_gbtidl_summary(path / "gbtidl" / "AGBT05B_047_01.summary")

        for col in cols.items():
            assert_series_equal(
                dysh_df[col[0]],  # .sort_values(),
                gbtidl_summary[col[1]],  # .sort_values(),
                check_dtype=False,
                check_names=False,
                check_index=False,
            )

    def test_contruct_integration_number(self):
        """Test that construction of integration number (intnum) during FITS load matches
        that in the GBTIDL index file
        """
        p = util.get_project_testdata() / "AGBT20B_014_03.raw.vegas"
        index_file = p / "AGBT20B_014_03.raw.vegas.A6.index"
        data_file = p / "AGBT20B_014_03.raw.vegas.A6.fits"
        g = gbtfitsload.GBTFITSLoad(data_file)
        gbtidl_index = pd.read_csv(index_file, skiprows=10, delim_whitespace=True)
        assert np.all(g._index["INTNUM"] == gbtidl_index["INT"])

    def test_getps_smoothref(self):
        """ """

        path = util.get_project_testdata() / "TGBT21A_501_11"
        data_file = path / "TGBT21A_501_11.raw.vegas.fits"
        gbtidl_file = path / "TGBT21A_501_11_getps_scan_152_ifnum_0_plnum_0_smthoff_15.fits"

        sdf = gbtfitsload.GBTFITSLoad(data_file)
        sb = sdf.getps(scan=152, ifnum=0, plnum=0, smoothref=15)
        ta = sb.timeaverage()

        hdu = fits.open(gbtidl_file)
        table = hdu[1].data
        hdu.close()
        gbtidl_spec = table["DATA"][0]

        diff = ta.flux.to("K").value.astype(np.float32) - gbtidl_spec

        assert np.all(abs(diff[~np.isnan(diff)]) < 7e-5)
        assert ta.meta["EXPOSURE"] == table["EXPOSURE"][0]
        for k, v in ta.meta.items():
            if k in ["DURATION", "TUNIT7", "VSPRPIX", "CAL"]:
                continue
            try:
                assert v == table[k][0]
            except KeyError:
                continue

    def test_write_single_file(self, tmp_path):
        "Test that writing an SDFITS file works when subselecting data"
        p = util.get_project_testdata() / "AGBT20B_014_03.raw.vegas"
        data_file = p / "AGBT20B_014_03.raw.vegas.A6.fits"
        g = gbtfitsload.GBTFITSLoad(data_file)
        o = tmp_path / "sub"
        o.mkdir()
        out = o / "test_write_single.fits"
        g.write(out, plnum=1, intnum=2, overwrite=True)
        t = gbtfitsload.GBTFITSLoad(out)
        assert set(t._index["PLNUM"]) == set([1])
        # assert set(t._index["INT"]) == set([2])  # this exists because GBTIDL wrote it
        assert set(t._index["INTNUM"]) == set([2])

    def test_write_multi_file(self, tmp_path):
        "Test that writing multiple SDFITS files works, including subselection of data"
        f = util.get_project_testdata() / "AGBT18B_354_03/AGBT18B_354_03.raw.vegas/"
        g = gbtfitsload.GBTFITSLoad(f)
        # writes testmultia0,1,2,3.fits
        o = tmp_path / "sub"
        o.mkdir()
        output = o / "testmulti.fits"
        g.write(output, multifile=True, scan=6, overwrite=True)
        # @todo remove test output files in a teardown method
        sdf = gbtfitsload.GBTFITSLoad(o)

    def test_write_all(self, tmp_path):
        """Test that we can write a loaded SDFITS file without any changes"""
        p = util.get_project_testdata() / "AGBT20B_014_03.raw.vegas"
        data_file = p / "AGBT20B_014_03.raw.vegas.A6.fits"
        org_sdf = gbtfitsload.GBTFITSLoad(data_file)
        d = tmp_path / "sub"
        d.mkdir()
        output = d / "test_write_all.fits"
        org_sdf.write(output, overwrite=True)
        new_sdf = gbtfitsload.GBTFITSLoad(output)
        # Compare the index for both SDFITS.
        assert_frame_equal(org_sdf._index, new_sdf._index)
