import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material ui  components
import IconButton from "@mui/material/IconButton";
import Card from "@mui/material/Card";
import CardActions from "@mui/material/CardActions";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import SettingsIcon from "@mui/icons-material/Build";
import DeleteIcon from "@mui/icons-material/Delete";
// jarr
import doFetchObjForEdit from "../../../hooks/doFetchObjForEdit";
import doDeleteObj from "../../../hooks/doDeleteObj";
import doListClusters from "../../../hooks/doListClusters";
import ClusterIcon from "../../../components/ClusterIcon";
import makeStyles from "./style";

const mapDispatchToProps = (dispatch) => ({
  openEditPanel(id, objType) {
    dispatch(doFetchObjForEdit(objType, id));
  },
  deleteObj(id, type) {
    dispatch(doDeleteObj(id, type));
    dispatch(doListClusters({ categoryId: "all" }));
  },
});

function SelectedObjCard({ id, str, type, iconUrl, errorCount, lastRetrieved,
                           openEditPanel, deleteObj }) {
  const objType = type === "feed" ? "feed" : "category";
  const classes = makeStyles();

  return (
    <Card variant="outlined" className={classes.clusterListCard}>
      <CardContent className={classes.clusterListCardTitle}>
        {type === "feed" ? <ClusterIcon iconUrl={iconUrl} /> : null}
        <Typography>{str}</Typography>
      </CardContent>
      <CardActions className={classes.clusterListCardActions}>
        <IconButton size="small"
          onClick={() => openEditPanel(id, objType)}
          className={classes.clusterListCardActionBtn}
      >
         <SettingsIcon size="small" />
        </IconButton>
        <IconButton size="small"
          onClick={() => deleteObj(id, objType)}
          className={classes.clusterListCardActionBtn}
      >
         <DeleteIcon size="small" />
        </IconButton>
      </CardActions>
    </Card>
   );
}

SelectedObjCard.propTypes = {
  id: PropTypes.number.isRequired,
  str: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  iconUrl: PropTypes.string,
  errorCount: PropTypes.number,
  lastRetrieved: PropTypes.string,
  openEditPanel: PropTypes.func.isRequired,
  deleteObj: PropTypes.func.isRequired,
};

export default connect(null, mapDispatchToProps)(SelectedObjCard);
