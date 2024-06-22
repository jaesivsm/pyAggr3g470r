import React from "react";
import PropTypes from "prop-types";
import { apiUrl } from "../const";
import qs from "qs";
import LinkIcon from "@mui/icons-material/Link";
import { Theme, createStyles } from "@mui/material/styles";
import { makeStyles } from "@mui/styles";

const iconStyle = makeStyles((theme: Theme) =>
  createStyles({
    clusterIcon: {
      maxWidth: 16,
      maxHeight: 16,
      margin: "8px 5px 8px 20px"
    },
  }),
);

function ClusterIcon({ iconUrl }) {
  const classes = iconStyle();
  if (iconUrl) {
    return <img className={classes.clusterIcon} alt="" src={
          `${apiUrl}/feed/icon?${qs.stringify({ url: iconUrl })}`} />;
  }
  return <LinkIcon className={classes.clusterIcon}
            color="disabled" fontSize="small"/>;
}

ClusterIcon.propTypes = {
  iconUrl: PropTypes.string
};

export default ClusterIcon;
