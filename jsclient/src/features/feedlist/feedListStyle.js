import { Theme, createStyles } from "@mui/material/styles";
import { makeStyles } from "@mui/styles";

import { feedListWidth } from "../../const";

export default makeStyles((theme: Theme) =>
  createStyles({
    drawer: {
      width: feedListWidth,
      [theme.breakpoints.down("sm")]: {
        width: "auto"
      },
      flexShrink: 0,
    },
    drawerPaper: {
      width: feedListWidth,
      [theme.breakpoints.down("sm")]: {
        width: "100%"
      },
    },
    drawerHeader: {
      display: "flex",
      alignItems: "center",
      padding: theme.spacing(0, 1),
      // necessary for content to be below app bar
      ...theme.mixins.toolbar,
      justifyContent: "space-between",
    },
    category: {
      paddingTop: 2,
      paddingBottom: 2,
    },
    catItem: {
      paddingLeft: 30,
      paddingRight: 10,
      [theme.breakpoints.down("sm")]: {
        paddingLeft: 30,
        paddingRight: 14
      }
    },
    catItemAll: {
      paddingLeft: 50,
    },
    catItemText: {
      marginLeft: 20
    },
    feedItem: {
      lineHeight: 1,
      overflow: "hidden",
      paddingLeft: "35px !important",
      whiteSpace: "nowrap",
      [theme.breakpoints.down("sm")]: {
        paddingRight: 14,
        paddingLeft: "40px !important",
      }
    },
    feedItemText: {
      marginRight: 10,
      [theme.breakpoints.down("sm")]: {
        marginRight: 25,
      },
      "& span" : {
        maxWidth: "100%",
        overflow: "hidden",
      }
    },
    feedBadge: {
      opacity: 0.6,
      right: 2
    },
    feed: {
      paddingTop: 2,
      paddingBottom: 2,
    },
    welcome: {
      "& .MuiAlert-icon": {
        display: "none",
      },
      "& .MuiAlert-message": {
        padding: 0,
      },
      "& svg": {
        height: 20,
        width: 20,
      },
      "& .MuiButtonBase-root": {
        height: 20,
        width: 20,
        padding: 0,
      },
    },
    foldButton: {
      opacity: 0.7,
      [theme.breakpoints.down("sm")]: {
        height: 40,
        width: 40,
      }
    },
    loadFeedList: {
      width: "100%",
      textAlign: "center",
      padding: "20px 0",
    }
  }),
);
