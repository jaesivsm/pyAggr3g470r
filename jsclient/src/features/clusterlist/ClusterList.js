import React, { useEffect, useState } from "react";
import clsx from "clsx";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material ui components
import { useTheme } from "@mui/material/styles";
import Fab from "@mui/material/Fab";
import useMediaQuery from "@mui/material/useMediaQuery";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Alert from "@mui/material/Alert";
import AddIcon from "@mui/icons-material/Add";
// jarr
import Cluster from "./components/Cluster";
import SelectedObjCard from "./components/SelectedObjCard";
import doLoadMoreClusters from "../../hooks/doLoadMoreClusters";
import doListClusters from "../../hooks/doListClusters";
import makeStyles from "./components/style";
import Articles from "./components/Articles";

const mapStateToProps = (state) => {
  let selectedFilterObj;
  if(state.clusters.filters["feed_id"]) {
    selectedFilterObj = state.feeds.feedListRows.filter((row) => (
      row.type === "feed" && row.id === state.clusters.filters["feed_id"]
    ))[0];
  } else if (state.clusters.filters["category_id"]) {
    selectedFilterObj = state.feeds.feedListRows.filter((row) => (
      row.type === "categ" && row.id === state.clusters.filters["category_id"]
    ))[0];
  }

  let clusters = [];
  if (!state.clusters.loading) {
    clusters = state.clusters.clusters.map((cluster) => `c-${cluster.id}`);
  }
  return { clusters,
           loadedCluster: state.clusters.loadedCluster,
           filters: state.clusters.filters,
           loading: state.clusters.loading,
           moreLoading: state.clusters.moreLoading,
           moreToFetch: state.clusters.moreToFetch,
           isFeedListOpen: state.feeds.isOpen,
           isEditPanelOpen: state.edit.isOpen,
           selectedFilterObj,
           doDisplayContent: (!!state.clusters.loadedCluster
              && !!state.clusters.requestedClusterId
              && !!state.clusters.loadedCluster.id
              && state.clusters.requestedClusterId === state.clusters.loadedCluster.id),
  };
};

const mapDispatchToProps = (dispatch) => ({
  listClusters(filters) {
    dispatch(doListClusters(filters));
  },
  loadMoreClusters() {
    dispatch(doLoadMoreClusters());
  },
});

const ClusterList = ({ clusters, filters, loadedCluster,
                       loading, doDisplayContent,
                       isFeedListOpen, isEditPanelOpen,
                       moreLoading, moreToFetch,
                       selectedFilterObj,
                       listClusters, loadMoreClusters, openEditPanel,
                       }) => {
  const theme = useTheme();
  const classes = makeStyles();
  const splitedMode = useMediaQuery(theme.breakpoints.up("md"));
  const isShifted = (isFeedListOpen === null ? splitedMode : isFeedListOpen) && !isEditPanelOpen;
  const contentClassName = clsx(classes.main,
    {[classes.mainShifted]: isShifted,
     [classes.mainSplitted]: splitedMode});
  const [everLoaded, setEverLoaded] = useState(false);
  useEffect(() => {
    if (!everLoaded) {
      setEverLoaded(true);
      listClusters(filters);
    }
  }, [everLoaded, filters, listClusters]);

  let list;
  let loadMoreButton;
  if (loading) {
    list = <div className={classes.loadingWrap}><CircularProgress /></div>;
  } else if (clusters.length) {
    list = clusters.map((cluster, index) => (
        <Cluster key={cluster} index={index} splitedMode={splitedMode} />));
    if (moreLoading && moreToFetch) {
      loadMoreButton = <CircularProgress />;
    } else if (moreToFetch) {
      loadMoreButton = (
        <Fab color="primary" className={classes.fab} onClick={loadMoreClusters}>
          <AddIcon />
        </Fab>
      );
    }
    loadMoreButton = (
      <div className={classes.clusterLoadMore}>
        {loadMoreButton}
      </div>
    );
  } else {
    list = (
      <Alert severity="info">
        Nothing to read with the current filter.
        Try adding more feeds or come back later!
      </Alert>
    );
  }
  let card;
  if (selectedFilterObj) {
    card = <SelectedObjCard
              id={selectedFilterObj.id}
              str={selectedFilterObj.str}
              type={selectedFilterObj.type}
              iconUrl={selectedFilterObj["icon_url"]}
              errorCount={selectedFilterObj["error_count"]}
              lastRetrieved={selectedFilterObj["last_retrieved"]}
            />;
  }

  if (!splitedMode) {
    return (
      <main className={contentClassName}>
        {card}
        {list}
        {loadMoreButton}
      </main>
    );
  }
  let content;
  if (doDisplayContent) {
    content = (
      <Paper className={clsx(classes.contentPanel,
                             {[classes.contentPanelShifted]: isShifted,})}>
        <div className={classes.contentPanelInner}>
          <Articles content={loadedCluster.contents}
                    articles={loadedCluster.articles} />
        </div>
      </Paper>
    );
  }
  return (
    <main className={contentClassName}>
      <div className={clsx(classes.clusterList,
                          {[classes.clusterListShifted]: isShifted,})}>
        <div className={classes.clusterListInner}>
          {card}
          {list}
          {loadMoreButton}
        </div>
      </div>
      {content}
    </main>
  );
};

ClusterList.propTypes = {
  clusters: PropTypes.array.isRequired,
  filters: PropTypes.object.isRequired,
  loading: PropTypes.bool.isRequired,
  isFeedListOpen: PropTypes.bool,
  isEditPanelOpen: PropTypes.bool.isRequired,
  listClusters: PropTypes.func.isRequired,
  selectedFilterObj: PropTypes.object,
  doDisplayContent: PropTypes.bool.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(ClusterList);
